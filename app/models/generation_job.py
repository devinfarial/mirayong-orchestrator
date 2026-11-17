from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStage(StrEnum):
    SCRIPT = "script"
    ASSETS = "assets"
    RENDER = "render"
    VALIDATE = "validate"
    PUBLISH = "publish"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class GenerationJob(Base):
    __tablename__ = "generation_job"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    episode_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("episode.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=JobStatus.PENDING.value,
        server_default=JobStatus.PENDING.value
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    provider_request_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    estimated_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0"
    )

    actual_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0"
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )