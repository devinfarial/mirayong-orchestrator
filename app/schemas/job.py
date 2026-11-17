from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenerationJobResponse(BaseModel):
    id: int
    episode_id: int
    stage: str
    status: str
    attempt_count: int
    provider_request_id: str | None
    error_code: str | None
    error_message: str | None
    estimated_cost: float
    actual_cost: float
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)