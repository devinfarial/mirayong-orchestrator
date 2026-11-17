from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SceneGenerationStatus(StrEnum):
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"


class Scene(Base):
    __tablename__ = "scene"

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

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    narration_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    visual_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    on_screen_text: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    video_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    audio_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    generation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SceneGenerationStatus.PENDING.value,
        server_default=SceneGenerationStatus.PENDING.value
    )

    provider_request_id: Mapped[str | None] = mapped_column(
        String(255),
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )