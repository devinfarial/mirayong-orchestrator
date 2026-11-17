from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cost_manager import CostManager
from app.core.state_machine import EpisodeStatus
from app.models.episode import Episode
from app.models.generation_job import GenerationJob, JobStage, JobStatus
from app.repositories.episode_repository import EpisodeRepository
from app.repositories.job_repository import JobRepository
from app.services.script_service import ScriptService
from app.services.asset_service import AssetService


class WorkflowError(Exception):
    """Raised when a workflow action cannot proceed."""


# Maps an episode's current status to the next JobStage and resulting EpisodeStatus
NEXT_STAGE_BY_STATUS: dict[EpisodeStatus, tuple[JobStage, EpisodeStatus]] = {
    EpisodeStatus.DRAFT: (JobStage.SCRIPT, EpisodeStatus.SCRIPT_READY),
    EpisodeStatus.SCRIPT_READY: (JobStage.ASSETS, EpisodeStatus.ASSETS_GENERATED),
    EpisodeStatus.ASSETS_GENERATED: (JobStage.RENDER, EpisodeStatus.RENDERED),
    EpisodeStatus.RENDERED: (JobStage.VALIDATE, EpisodeStatus.VALIDATED),
    EpisodeStatus.VALIDATED: (JobStage.PUBLISH, EpisodeStatus.PUBLISHED),
}

# Maps a failed JobStage back to the EpisodeStatus needed to retry it
RETRY_STATUS_BY_STAGE: dict[JobStage, EpisodeStatus] = {
    JobStage.SCRIPT: EpisodeStatus.DRAFT,
    JobStage.ASSETS: EpisodeStatus.SCRIPT_READY,
    JobStage.RENDER: EpisodeStatus.ASSETS_GENERATED,
    JobStage.VALIDATE: EpisodeStatus.RENDERED,
    JobStage.PUBLISH: EpisodeStatus.VALIDATED,
}


class WorkflowOrchestrator:

    @staticmethod
    def resolve_next_stage(
        episode: Episode
    ) -> tuple[JobStage, EpisodeStatus]:
        try:
            current_status = EpisodeStatus(episode.status)
        except ValueError as e:
            raise WorkflowError(f"Unknown episode status: {episode.status}") from e

        if current_status not in NEXT_STAGE_BY_STATUS:
            raise WorkflowError(
                f"Episode in '{current_status}' status has no next stage to run "
                f"(use retry if failed)"
            )

        return NEXT_STAGE_BY_STATUS[current_status]

    @staticmethod
    async def run_next_stage(
        db: AsyncSession,
        episode_id: int
    ) -> GenerationJob:
        episode = await EpisodeRepository.get_by_id(db, episode_id)
        if episode is None:
            raise LookupError(f"Episode with ID {episode_id} not found")

        stage, target_status = WorkflowOrchestrator.resolve_next_stage(episode)

        # Idempotency check: if a job for this stage is already running, return it
        existing_jobs = await JobRepository.get_by_episode_id(db, episode_id)
        for existing in existing_jobs:
            if existing.stage == stage.value and existing.status == JobStatus.RUNNING.value:
                return existing

        # 1. Estimate cost & enforce budget cap BEFORE creating/running the job
        estimated_cost = CostManager.estimate_stage_cost(stage, episode.script_json)
        await CostManager.check_budget(db, estimated_cost)

        # 2. Create job record and mark running
        job = await JobRepository.create(
            db,
            episode_id=episode.id,
            stage=stage,
            estimated_cost=estimated_cost
        )
        job = await JobRepository.mark_running(db, job)

        # 3. Execute stage logic
        try:
            actual_cost = await WorkflowOrchestrator._execute_stage(
                db, episode, stage, target_status, estimated_cost
            )
            job = await JobRepository.mark_succeeded(
                db, job, actual_cost=actual_cost
            )
            return job

        except Exception as e:
            await EpisodeRepository.transition_status(
                db, episode, EpisodeStatus.FAILED
            )
            await JobRepository.mark_failed(
                db,
                job,
                error_message=str(e),
                error_code=type(e).__name__
            )
            raise

    @staticmethod
    async def _execute_stage(
        db: AsyncSession,
        episode: Episode,
        stage: JobStage,
        target_status: EpisodeStatus,
        estimated_cost: float
    ) -> float:
        if stage == JobStage.SCRIPT:
            await ScriptService.generate_script(db, episode.id)
            return estimated_cost

        if stage == JobStage.ASSETS:
            return await AssetService.generate_episode_assets(db, episode.id)

        # Placeholder for Milestones 5 & 6 (Render, Validate, Publish):
        await EpisodeRepository.transition_status(db, episode, target_status)
        return estimated_cost

    @staticmethod
    async def retry_failed_episode(
        db: AsyncSession,
        episode_id: int
    ) -> GenerationJob:
        episode = await EpisodeRepository.get_by_id(db, episode_id)
        if episode is None:
            raise LookupError(f"Episode with ID {episode_id} not found")

        if episode.status != EpisodeStatus.FAILED.value:
            raise WorkflowError(
                f"Only 'failed' episodes can be retried (current: '{episode.status}')"
            )

        jobs = await JobRepository.get_by_episode_id(db, episode_id)
        failed_job = next(
            (j for j in jobs if j.status == JobStatus.FAILED.value),
            None
        )
        if failed_job is None:
            raise WorkflowError("No failed job found to determine retry stage")

        failed_stage = JobStage(failed_job.stage)
        recovery_status = RETRY_STATUS_BY_STAGE[failed_stage]

        # Restore the episode to the pre-failure status and re-run that stage
        await EpisodeRepository.transition_status(db, episode, recovery_status)
        return await WorkflowOrchestrator.run_next_stage(db, episode_id)
