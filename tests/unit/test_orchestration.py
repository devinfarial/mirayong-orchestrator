import pytest

from app.models.generation_job import JobStage, JobStatus
from app.services.script_service import ScriptGenerationError, ScriptService
from tests.test_episode import client  # noqa: F401
from tests.unit.test_script_service import VALID_SCRIPT


async def test_orchestrator_runs_script_and_recovers_from_failure(
    client, monkeypatch
):
    # 1. Create a draft episode via API
    create_resp = await client.post(
        "/api/v1/episodes",
        json={"title": "Test Workflow", "topic": "Colors"}
    )
    episode_id = create_resp.json()["id"]

    # 2. Simulate first script generation failing
    calls = {"count": 0}

    async def flaky_generate_script(db, ep_id, ai=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ScriptGenerationError("Simulated provider timeout")
        # Second attempt succeeds
        from app.repositories.episode_repository import EpisodeRepository
        ep = await EpisodeRepository.get_by_id(db, ep_id)
        return await EpisodeRepository.save_script(db, ep, VALID_SCRIPT)

    monkeypatch.setattr(ScriptService, "generate_script", flaky_generate_script)

    # First call fails -> 502 Bad Gateway, episode becomes 'failed'
    gen_resp = await client.post(f"/api/v1/episodes/{episode_id}/generate")
    assert gen_resp.status_code == 502

    status_resp = await client.get(f"/api/v1/episodes/{episode_id}/status")
    status_data = status_resp.json()
    assert status_data["status"] == "failed"
    assert status_data["jobs"][0]["status"] == JobStatus.FAILED.value
    assert status_data["jobs"][0]["stage"] == JobStage.SCRIPT.value

    # 3. Retry the failed episode -> succeeds and transitions to 'script_ready'
    retry_resp = await client.post(f"/api/v1/episodes/{episode_id}/retry")
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] == JobStatus.SUCCEEDED.value

    final_status = await client.get(f"/api/v1/episodes/{episode_id}/status")
    assert final_status.json()["status"] == "script_ready"
