import copy
import json
from pathlib import Path

from tests.test_episode import client  # noqa: F401
from tests.unit.test_script_service import VALID_SCRIPT


def _unique_script() -> dict:
    """Return VALID_SCRIPT with distinct visual prompts per scene."""
    script = copy.deepcopy(VALID_SCRIPT)
    for idx, scene in enumerate(script["scenes"], start=1):
        scene["visual_prompt"] = (
            f"Scene {idx}: A friendly round fox in a sunny meadow, colorful 3D animation"
        )
    return script


async def test_render_and_validate_pipeline(
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

    # 1. Create episode
    ep_resp = await client.post(
        "/api/v1/episodes",
        json={"title": "Render Test", "topic": "Colors"}
    )
    episode_id = ep_resp.json()["id"]

    # 2. Run stage 1: SCRIPT -> status becomes 'script_ready'
    r1 = await client.post(f"/api/v1/episodes/{episode_id}/generate")
    assert r1.status_code == 200
    assert r1.json()["stage"] == "script"

    # 3. Run stage 2: ASSETS -> status becomes 'assets_generated'
    r2 = await client.post(f"/api/v1/episodes/{episode_id}/generate")
    assert r2.status_code == 200
    assert r2.json()["stage"] == "assets"

    # 4. Run stage 3: RENDER -> status becomes 'rendered' and render_path exists
    r3 = await client.post(f"/api/v1/episodes/{episode_id}/generate")
    assert r3.status_code == 200
    assert r3.json()["stage"] == "render"

    ep_after_render = (await client.get(f"/api/v1/episodes/{episode_id}")).json()
    assert ep_after_render["status"] == "rendered"
    assert Path(ep_after_render["render_path"]).exists()

    # 5. Run stage 4: VALIDATE -> status becomes 'validated'
    r4 = await client.post(f"/api/v1/episodes/{episode_id}/generate")
    assert r4.status_code == 200
    assert r4.json()["stage"] == "validate"

    ep_after_val = (await client.get(f"/api/v1/episodes/{episode_id}")).json()
    assert ep_after_val["status"] == "validated"