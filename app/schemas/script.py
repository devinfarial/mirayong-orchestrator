from pydantic import BaseModel, Field, model_validator

MIN_SCENES = 3
MAX_SCENES = 6
MAX_TOTAL_SECONDS = 40
MIN_TOTAL_SECONDS = 15


class ScriptScene(BaseModel):
    sequence_number: int = Field(ge=1)
    narration_text: str = Field(min_length=1, max_length=400)
    visual_prompt: str = Field(min_length=10, max_length=800)
    duration_seconds: float = Field(gt=0, le=15)
    on_screen_text: str | None = Field(default=None, max_length=60)


class EpisodeScript(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    learning_objective: str = Field(min_length=1, max_length=300)
    target_age_band: str = Field(min_length=1, max_length=20)
    hook: str = Field(min_length=1, max_length=200)
    scenes: list[ScriptScene] = Field(min_length=MIN_SCENES, max_length=MAX_SCENES)
    closing_recap: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def check_timeline(self) -> "EpisodeScript":
        numbers = [scene.sequence_number for scene in self.scenes]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(
                "scene sequence_number values must run 1..N in order"
            )

        total = sum(scene.duration_seconds for scene in self.scenes)
        if not MIN_TOTAL_SECONDS <= total <= MAX_TOTAL_SECONDS:
            raise ValueError(
                f"total duration must be {MIN_TOTAL_SECONDS}-"
                f"{MAX_TOTAL_SECONDS}s, got {total:.1f}s"
            )

        return self

    @property
    def total_duration_seconds(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)
