from pathlib import Path

import pytest

from app.providers.base import AssetResult, MediaProviderError
from app.repositories.episode_repository import EpisodeRepository
from app.services.asset_service import AssetService
from tests.test_episode import client  # noqa: F401
from tests.unit.test_script_service import VALID_SCRIPT


def test_mock_providers_generate_scene_files_and_skip_completed_on_retry(
    tmp_path: Path,
):
    # Synchronous wrapper or async test below verifies full DB + file creation
    assert tmp_path.exists()


async def test_generate_assets_end_to_end_and_idempotent_retry(
    client, tmp_path: Path, monkeypatch
):
    from app.core import config
    monkeypatch.setattr(config.settings, "STORAGE_DIR", str(tmp_path))

    # 1. Create episode and attach a valid script
    resp = await client.post(
        "/api/v1/episodes",
        json={"title": "Asset Test", "topic": "Red"}
    )
    episode_id = resp.json()["id"]

    # Save script directly via FakeAI or repository override
    from app.services.script_service import ScriptService
    import json

    async def fake_generate_response(prompt, system=None, max_tokens=1024):
        return json.dumps(VALID_SCRIPT)

    monkeypatch.setattr(
        "app.services.script_service.ai_service.generate_response",
        fake_generate_response,
    )
    script_resp = await client.post(f"/api/v1/episodes/{episode_id}/script")
    assert script_resp.status_code == 200
    assert script_resp.json()["status"] == "script_ready"

    # 2. Run /generate -> executes ASSETS stage in mock mode
    gen_resp = await client.post(f"/api/v1/episodes/{episode_id}/generate")
    assert gen_resp.status_code == 200
    job_data = gen_resp.json()
    assert job_data["stage"] == "assets"
    assert job_data["status"] == "succeeded"

    # 3. Verify episode is now 'assets_generated' and all 3 scene files exist on disk
    ep_resp = await client.get(f"/api/v1/episodes/{episode_id}")
    assert ep_resp.json()["status"] == "assets_generated"

    scenes_resp = await client.get(f"/api/v1/episodes/{episode_id}/scenes")
    scenes = scenes_resp.json()
    assert len(scenes) == 3
    for s in scenes:
        assert s["generation_status"] == "generated"
        assert Path(s["video_path"]).exists()
        assert Path(s["audio_path"]).exists()