from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.state_machine import EpisodeStatus
from app.providers.youtube import (
    YouTubeProvider,
    YouTubePublishError,
    YouTubeUploadResult,
)
from app.repositories.episode_repository import EpisodeRepository


class PublishingService:

    @staticmethod
    async def publish_episode(
        db: AsyncSession,
        episode_id: int,
        provider: YouTubeProvider | None = None,
    ) -> YouTubeUploadResult:
        """
        Queue and upload a validated episode to YouTube Shorts.
        Idempotent: if youtube_video_id is already recorded, returns it without re-uploading.
        """
        episode = await EpisodeRepository.get_by_id(db, episode_id)
        if episode is None:
            raise LookupError(f"Episode with ID {episode_id} not found")

        # Idempotency guard: prevent duplicate uploads on retry
        if episode.youtube_video_id:
            return YouTubeUploadResult(
                video_id=episode.youtube_video_id,
                video_url=f"https://youtube.com/shorts/{episode.youtube_video_id}",
            )

        if not episode.render_path or not Path(episode.render_path).exists():
            raise YouTubePublishError(
                f"Episode {episode_id} has no valid rendered MP4 to upload"
            )

        # Transition VALIDATED -> PUBLISH_QUEUED before starting external upload
        if episode.status == EpisodeStatus.VALIDATED.value:
            episode = await EpisodeRepository.transition_status(
                db, episode, EpisodeStatus.PUBLISH_QUEUED
            )

        script = episode.script_json or {}
        title = script.get("title") or episode.title
        closing_recap = script.get("closing_recap") or ""
        learning_obj = script.get("learning_objective") or ""
        description = "\n\n".join(
            part for part in (closing_recap, learning_obj, episode.description or "") if part
        )

        yt = provider or YouTubeProvider()
        result = await yt.upload_video(
            video_path=Path(episode.render_path),
            title=title,
            description=description,
            language=episode.language or settings.DEFAULT_LANGUAGE,
        )

        episode.youtube_video_id = result.video_id
        await EpisodeRepository.transition_status(
            db, episode, EpisodeStatus.PUBLISHED
        )

        return result
