from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.state_machine import EpisodeStatus
from app.models.scene import SceneGenerationStatus
from app.providers.base import AssetResult, VideoProvider, VoiceProvider
from app.providers.elevenlabs import ElevenLabsProvider
from app.providers.gemini_media import GeminiVideoProvider, GeminiVoiceProvider
from app.providers.higgsfield import HiggsfieldProvider
from app.repositories.episode_repository import EpisodeRepository
from app.repositories.scene_repository import SceneRepository


class AssetGenerationError(Exception):
    """Raised when scene video/voice assets cannot be generated."""


def resolve_voice_provider() -> VoiceProvider:
    mode = settings.VOICE_PROVIDER.lower()
    if mode == "gemini":
        return GeminiVoiceProvider()
    return ElevenLabsProvider(mode=mode)


def resolve_video_provider() -> VideoProvider:
    mode = settings.VIDEO_PROVIDER.lower()
    if mode == "gemini":
        return GeminiVideoProvider()
    return HiggsfieldProvider(mode=mode)


class AssetService:

    @staticmethod
    async def generate_episode_assets(
        db: AsyncSession,
        episode_id: int,
        video_provider: VideoProvider | None = None,
        voice_provider: VoiceProvider | None = None,
        storage_root: Path | None = None,
    ) -> float:
        """
        Generate missing video and voice assets for all scenes of an episode.
        Reuses real files on disk (> 1KB) if already present so no credits are wasted.
        """
        episode = await EpisodeRepository.get_by_id(db, episode_id)
        if episode is None:
            raise LookupError(f"Episode with ID {episode_id} not found")

        if not episode.script_json:
            raise AssetGenerationError(
                f"Episode {episode_id} has no script_json; generate script first"
            )

        video_adapter = video_provider or resolve_video_provider()
        voice_adapter = voice_provider or resolve_voice_provider()
        base_dir = storage_root or Path(settings.STORAGE_DIR)

        scenes = await SceneRepository.sync_from_script(
            db, episode.id, episode.script_json
        )

        total_actual_cost = 0.0

        for scene in scenes:
            # Idempotency: reuse already-generated scene assets if files exist on disk
            if (
                scene.generation_status == SceneGenerationStatus.GENERATED.value
                and scene.video_path
                and scene.audio_path
                and Path(scene.video_path).exists()
                and Path(scene.audio_path).exists()
            ):
                continue

            audio_out = (
                base_dir
                / "audio"
                / f"episode_{episode.id}_scene_{scene.sequence_number}.mp3"
            )
            video_out = (
                base_dir
                / "generated"
                / f"episode_{episode.id}_scene_{scene.sequence_number}.mp4"
            )

            # Reuse real audio file on disk if already present (> 1 KB)
            if audio_out.exists() and audio_out.stat().st_size > 1024:
                voice_res = AssetResult(
                    file_path=str(audio_out),
                    provider_request_id="reused-disk-audio",
                    actual_cost=0.0,
                )
            else:
                voice_res = await voice_adapter.synthesize_speech(
                    text=scene.narration_text,
                    output_path=audio_out,
                    language=episode.language or settings.DEFAULT_LANGUAGE,
                )

            # Reuse real video file on disk if already present (> 1 KB)
            if video_out.exists() and video_out.stat().st_size > 1024:
                video_res = AssetResult(
                    file_path=str(video_out),
                    provider_request_id="reused-disk-video",
                    actual_cost=0.0,
                )
            else:
                video_res = await video_adapter.generate_clip(
                    visual_prompt=scene.visual_prompt,
                    duration_seconds=scene.duration_seconds,
                    output_path=video_out,
                )

            scene_cost = round(voice_res.actual_cost + video_res.actual_cost, 4)
            combined_req_id = f"{voice_res.provider_request_id}|{video_res.provider_request_id}"

            await SceneRepository.update_assets(
                db,
                scene=scene,
                video_path=video_res.file_path,
                audio_path=voice_res.file_path,
                actual_cost=scene_cost,
                provider_request_id=combined_req_id,
            )

            total_actual_cost = round(total_actual_cost + scene_cost, 4)

        await EpisodeRepository.transition_status(
            db, episode, EpisodeStatus.ASSETS_GENERATED
        )

        return total_actual_cost
