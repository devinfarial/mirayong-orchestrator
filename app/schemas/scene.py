from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SceneResponse(BaseModel):
    id: int
    episode_id: int
    sequence_number: int
    narration_text: str
    visual_prompt: str
    on_screen_text: str | None
    duration_seconds: float
    video_path: str | None
    audio_path: str | None
    generation_status: str
    provider_request_id: str | None
    estimated_cost: float
    actual_cost: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)