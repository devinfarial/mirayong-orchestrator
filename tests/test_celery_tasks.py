from types import SimpleNamespace

from app.core.orchestration import WorkflowOrchestrator
from app.workers import tasks


def test_run_next_stage_task_invokes_orchestrator(monkeypatch):
    fake_job = SimpleNamespace(
        id=42,
        episode_id=3,
        stage="script",
        status="succeeded",
    )

    async def fake_run_stage_async(episode_id: int) -> dict:
        return {
            "job_id": fake_job.id,
            "episode_id": episode_id,
            "stage": fake_job.stage,
            "status": fake_job.status,
        }

    monkeypatch.setattr(tasks, "_run_stage_async", fake_run_stage_async)

    result = tasks.run_next_stage_task(3)

    assert result == {
        "job_id": 42,
        "episode_id": 3,
        "stage": "script",
        "status": "succeeded",
    }