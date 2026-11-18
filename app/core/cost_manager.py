from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.generation_job import JobStage
from app.repositories.job_repository import JobRepository
from app.schemas.script import EpisodeScript


class BudgetExceededError(Exception):
    """Raised when an estimated job cost would exceed the configured budget."""


class CostManager:

    @staticmethod
    def estimate_script_cost() -> float:
        return round(settings.SCRIPT_ESTIMATED_COST_USD, 4)

    @staticmethod
    def estimate_assets_cost(script: EpisodeScript | dict) -> float:
        """Estimate video + voice TTS cost for all scenes in a script."""
        if isinstance(script, dict):
            script = EpisodeScript.model_validate(script)

        total_seconds = sum(scene.duration_seconds for scene in script.scenes)
        video_cost = total_seconds * settings.VIDEO_COST_PER_SECOND_USD

        total_chars = sum(len(scene.narration_text) for scene in script.scenes)
        tts_cost = (total_chars / 1000.0) * settings.TTS_COST_PER_1K_CHARS_USD

        return round(video_cost + tts_cost, 4)

    @staticmethod
    def estimate_stage_cost(
        stage: JobStage | str,
        script_json: dict | None = None
    ) -> float:
        stage_enum = JobStage(stage)
        if stage_enum == JobStage.SCRIPT:
            return CostManager.estimate_script_cost()
        if stage_enum == JobStage.ASSETS and script_json:
            return CostManager.estimate_assets_cost(script_json)
        return 0.0

    @staticmethod
    async def check_budget(
        db: AsyncSession,
        estimated_cost: float,
        now: datetime | None = None
    ) -> float:
        """
        Verify that estimated_cost fits within both per-episode and monthly limits.
        Returns projected monthly spend if allowed, or raises BudgetExceededError.
        """
        if estimated_cost > settings.MAX_EPISODE_COST_USD:
            raise BudgetExceededError(
                f"Estimated cost ${estimated_cost:.2f} exceeds per-episode cap "
                f"of ${settings.MAX_EPISODE_COST_USD:.2f}"
            )

        current_time = now or datetime.now(timezone.utc)
        current_spend = await JobRepository.get_monthly_spend(
            db,
            year=current_time.year,
            month=current_time.month
        )
        projected = round(current_spend + estimated_cost, 4)

        if projected > settings.MONTHLY_BUDGET_USD:
            raise BudgetExceededError(
                f"Projected monthly spend ${projected:.2f} (current ${current_spend:.2f} "
                f"+ estimated ${estimated_cost:.2f}) exceeds monthly budget "
                f"of ${settings.MONTHLY_BUDGET_USD:.2f}"
            )

        return projected

    @staticmethod
    async def get_monthly_report(
        db: AsyncSession,
        now: datetime | None = None
    ) -> dict:
        current_time = now or datetime.now(timezone.utc)
        current_spend = await JobRepository.get_monthly_spend(
            db,
            year=current_time.year,
            month=current_time.month
        )
        budget = settings.MONTHLY_BUDGET_USD
        remaining = round(max(0.0, budget - current_spend), 4)
        utilization_pct = round((current_spend / budget) * 100.0, 2) if budget > 0 else 0.0

        alerts: list[str] = []
        if budget > 0 and (current_spend / budget) >= settings.BUDGET_ALERT_THRESHOLD_PCT:
            alerts.append(
                f"BUDGET_THRESHOLD_WARNING: Monthly spend ${current_spend:.2f} has reached "
                f"{utilization_pct:.1f}% of ${budget:.2f} budget"
            )

        return {
            "year": current_time.year,
            "month": current_time.month,
            "budget_usd": budget,
            "current_spend_usd": round(current_spend, 4),
            "remaining_budget_usd": remaining,
            "utilization_pct": utilization_pct,
            "alerts": alerts,
        }
