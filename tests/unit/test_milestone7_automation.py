import json
from pathlib import Path

from app.repositories.job_repository import JobRepository
from tests.test_episode import client  # noqa: F401
from tests.unit.test_rendering_and_validation import _unique_script


async def test_monthly_cost_report_includes_budget_alert(client, monkeypatch):
    async def fake_spend(db, year, month):
        return 21.0  # 84% of $25 budget

    monkeypatch.setattr(JobRepository, "get_monthly_spend", fake_spend)

    resp = await client.get("/api/v1/jobs/report/monthly")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_spend_usd"] == 21.0
    assert data["remaining_budget_usd"] == 4.0
    assert len(data["alerts"]) == 1
    assert "BUDGET_THRESHOLD_WARNING" in data["alerts"][0]


async def test_run_pipeline_stops_at_validated_when_unattended_publish_disabled(
    client, tmp_path: Path, monkeypatch
):
    from app.core import config
    monkeypatch.setattr(config.settings, "STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(config.settings, "ALLOW_UNATTENDED_PUBLISH", False)

    async def fake_generate_response(prompt, system=None, max_tokens=1024):
        return json.dumps(_unique_script())

    monkeypatch.setattr(
        "app.services.script_service.ai_service.generate_response",
        fake_generate_response,
    )

    ep_resp = await client.post(
        "/api/v1/episodes",
        json={"title": "Autopilot Gate Test", "topic": "Shapes"}
    )
    episode_id = ep_resp.json()["id"]

    # Run autopilot pipeline -> should run script, assets, render, validate and pause before publish
    pipe_resp = await client.post(f"/api/v1/episodes/{episode_id}/run-pipeline")
    assert pipe_resp.status_code == 200
    jobs = pipe_resp.json()
    assert [j["stage"] for j in jobs] == ["script", "assets", "render", "validate"]

    ep = (await client.get(f"/api/v1/episodes/{episode_id}")).json()
    assert ep["status"] == "validated"
    assert ep["youtube_video_id"] is None
