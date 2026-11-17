import pytest

from app.core import cost_manager
from app.core.cost_manager import BudgetExceededError, CostManager
from app.repositories.job_repository import JobRepository

SAMPLE_SCRIPT = {
    "title": "Ayo Cari Warna Merah!",
    "learning_objective": "Mengenali warna merah",
    "target_age_band": "4-6",
    "hook": "Rubah Rudi ingin main!",
    "scenes": [
        {
            "sequence_number": 1,
            "narration_text": "Hai teman-teman! Aku Rubah Rudi.",
            "visual_prompt": "A friendly small fox character waving in a garden, 3D animation",
            "duration_seconds": 5,
            "on_screen_text": "Rubah Rudi",
        },
        {
            "sequence_number": 2,
            "narration_text": "Lihat! Ini apel merah.",
            "visual_prompt": "A friendly small fox character holding a red apple, 3D animation",
            "duration_seconds": 5,
            "on_screen_text": "Apel Merah",
        },
        {
            "sequence_number": 3,
            "narration_text": "Wah, ada bunga mawar merah!",
            "visual_prompt": "A friendly small fox character sniffing a red rose, 3D animation",
            "duration_seconds": 10,
            "on_screen_text": "Mawar Merah",
        },
    ],
    "closing_recap": "Teman-teman sudah belajar warna merah!",
}


def test_estimate_assets_cost_calculates_video_and_tts():
    # 20 seconds total * $0.15/s = $3.00 + tiny TTS character cost
    cost = CostManager.estimate_assets_cost(SAMPLE_SCRIPT)
    assert cost > 3.00
    assert cost < 3.10


async def test_check_budget_allows_within_cap(monkeypatch):
    async def fake_monthly_spend(db, year, month):
        return 10.0

    monkeypatch.setattr(JobRepository, "get_monthly_spend", fake_monthly_spend)

    projected = await CostManager.check_budget(None, estimated_cost=3.50)
    assert projected == 13.50


async def test_check_budget_blocks_when_monthly_cap_exceeded(monkeypatch):
    async def fake_monthly_spend(db, year, month):
        return 23.0

    monkeypatch.setattr(JobRepository, "get_monthly_spend", fake_monthly_spend)

    with pytest.raises(BudgetExceededError, match="monthly budget"):
        await CostManager.check_budget(None, estimated_cost=3.50)


async def test_check_budget_blocks_when_per_episode_cap_exceeded(monkeypatch):
    monkeypatch.setattr(cost_manager.settings, "MAX_EPISODE_COST_USD", 5.0)

    with pytest.raises(BudgetExceededError, match="per-episode cap"):
        await CostManager.check_budget(None, estimated_cost=6.0)
