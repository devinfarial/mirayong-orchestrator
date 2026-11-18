import json
from pathlib import Path

from app.providers.youtube import YouTubeProvider
from tests.test_episode import client  # noqa: F401
from tests.unit.test_rendering_and_validation import _unique_script


def test_youtube_metadata_sets_indonesian_and_made_for_kids():
    meta = YouTubeProvider.build_metadata(
        title="Ayo Cari Warna Merah!",
        description="Belajar warna merah bersama Rubah Rudi.",
        language="id",
    )
    assert meta["snippet"]["defaultLanguage"] == "id"
    assert meta["snippet"]["defaultAudioLanguage"] == "id"
    assert "#Shorts" in meta["snippet"]["title"]
    assert meta["status"]["selfDeclaredMadeForKids"] is True


async def test_full_pipeline_from_draft_to_published(
    client, tmp_path: Path, monkeypatch
):
    from app.core import config
    monkeypatch.setattr(config.settings, "STORAGE_DIR", str(tmp_path))

    async def fake_generate_response(prompt, system=None, max_tokens=1024):
        return json.dumps(_unique_script())

    monkeypatch.setattr(
        "app.services.script_service.ai_service.generate_response",
        fake_generate_response,
    )

    # Create draft episode
    ep_resp = await client.post(
        "/api/v1/episodes",
        json={"title": "Full Pipeline Short", "topic": "Red"}
    )
    episode_id = ep_resp.json()["id"]

    # Advance through all 5 stages: script -> assets -> render -> validate -> publish
    expected_stages = ["script", "assets", "render", "validate", "publish"]
    for expected_stage in expected_stages:
        resp = await client.post(f"/api/v1/episodes/{episode_id}/generate")
        assert resp.status_code == 200
        assert resp.json()["stage"] == expected_stage
        assert resp.json()["status"] == "succeeded"

    # Verify final episode is PUBLISHED with a youtube_video_id
    final_ep = (await client.get(f"/api/v1/episodes/{episode_id}")).json()
    assert final_ep["status"] == "published"
    assert final_ep["youtube_video_id"].startswith("yt_mock_")
