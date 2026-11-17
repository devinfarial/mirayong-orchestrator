from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generation_job import GenerationJob, JobStage, JobStatus


class JobRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        episode_id: int,
        stage: JobStage | str,
        estimated_cost: float = 0.0
    ) -> GenerationJob:
        job = GenerationJob(
            episode_id=episode_id,
            stage=str(stage),
            status=JobStatus.PENDING.value,
            estimated_cost=estimated_cost,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        job_id: int
    ) -> GenerationJob | None:
        result = await db.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_episode_id(
        db: AsyncSession,
        episode_id: int
    ) -> list[GenerationJob]:
        result = await db.execute(
            select(GenerationJob)
            .where(GenerationJob.episode_id == episode_id)
            .order_by(GenerationJob.id.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_running(
        db: AsyncSession,
        job: GenerationJob
    ) -> GenerationJob:
        job.status = JobStatus.RUNNING.value
        job.attempt_count += 1
        job.started_at = datetime.now(timezone.utc)
        job.error_code = None
        job.error_message = None

        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def mark_succeeded(
        db: AsyncSession,
        job: GenerationJob,
        actual_cost: float = 0.0,
        provider_request_id: str | None = None
    ) -> GenerationJob:
        job.status = JobStatus.SUCCEEDED.value
        job.actual_cost = actual_cost
        if provider_request_id is not None:
            job.provider_request_id = provider_request_id
        job.finished_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        job: GenerationJob,
        error_message: str,
        error_code: str = "STAGE_ERROR"
    ) -> GenerationJob:
        job.status = JobStatus.FAILED.value
        job.error_code = error_code
        job.error_message = error_message
        job.finished_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_monthly_spend(
        db: AsyncSession,
        year: int,
        month: int
    ) -> float:
        """Sum actual_cost of succeeded jobs + estimated_cost of pending/running jobs in the given UTC month."""
        start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            start_of_next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            start_of_next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.created_at >= start_of_month,
                GenerationJob.created_at < start_of_next_month,
            )
        )
        jobs = result.scalars().all()

        total = 0.0
        for job in jobs:
            if job.status == JobStatus.SUCCEEDED.value:
                total += job.actual_cost
            elif job.status in (JobStatus.PENDING.value, JobStatus.RUNNING.value):
                total += job.estimated_cost
        return total