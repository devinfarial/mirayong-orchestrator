
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.script import EpisodeScript


class EpisodeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    topic: str | None = Field(default=None, min_length=1, max_length=255)
    target_age_band: str | None = Field(default=None, min_length=1, max_length=20)


class EpisodeResponse(BaseModel):
    id: int
    title: str
    description: str | None
    topic: str | None
    target_age_band: str | None
    status: str
    script_json: EpisodeScript | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EpisodeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    topic: str | None = Field(default=None, min_length=1, max_length=255)
    target_age_band: str | None = Field(default=None, min_length=1, max_length=20)
    status: str | None = None
