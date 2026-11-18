
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.job import GenerationJobResponse
from app.schemas.script import EpisodeScript


class EpisodeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    topic: str | None = Field(default=None, min_length=1, max_length=255)
    target_age_band: str | None = Field(default=None, min_length=1, max_length=20)
    language: str = Field(default="id", min_length=2, max_length=10)


class EpisodeResponse(BaseModel):
    id: int
    title: str
    description: str | None
    topic: str | None
    target_age_band: str | None
    language: str
    status: str
    script_json: EpisodeScript | None
    render_path: str | None = None
    youtube_video_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EpisodeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    topic: str | None = Field(default=None, min_length=1, max_length=255)
    target_age_band: str | None = Field(default=None, min_length=1, max_length=20)
    status: str | None = None
    language: str | None = Field(default=None, min_length=2, max_length=10)


class EpisodeStatusResponse(BaseModel):
    episode_id: int
    status: str
    jobs: list[GenerationJobResponse]
