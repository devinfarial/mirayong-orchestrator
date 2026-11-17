import asyncio

from app.core.orchestration import WorkflowOrchestrator
from app.db.session import AsyncSessionLocal
from app.workers.celery_app import celery_app


async def _run_stage_async(episode_id: int) -> dict:
    async with AsyncSessionLocal() as db:
        job = await WorkflowOrchestrator.run_next_stage(db, episode_id)
        return {
            "job_id": job.id,
            "episode_id": job.episode_id,
            "stage": job.stage,
            "status": job.status,
        }


@celery_app.task(
    name="episodes.run_next_stage",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def run_next_stage_task(self, episode_id: int) -> dict:
    """Background Celery task to execute the next workflow stage for an episode."""
    return asyncio.run(_run_stage_async(episode_id))