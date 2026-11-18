from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.state_machine import EpisodeStatus
from app.models.scene import SceneGenerationStatus
from app.repositories.episode_repository import EpisodeRepository
from app.repositories.scene_repository import SceneRepository
from app.schemas.script import EpisodeScript

# Basic child-safety blocklist (Indonesian & English unsafe terms)
UNSAFE_TERMS = {
    "bunuh",
    "darah",
    "senjata",
    "pisau",
    "racun",
    "bahaya",
    "blood",
    "weapon",
    "knife",
    "poison",
}


class ValidationFailedError(Exception):
    """Raised when a rendered episode fails technical or content-safety checks."""


class ValidationService:

    @staticmethod
    async def validate_episode(
        db: AsyncSession,
        episode_id: int
    ) -> bool:
        """
        Run technical and content-safety checks on a rendered episode.
        Transitions episode to VALIDATED if all checks pass, else raises ValidationFailedError.
        """
        episode = await EpisodeRepository.get_by_id(db, episode_id)
        if episode is None:
            raise LookupError(f"Episode with ID {episode_id} not found")

        # 1. Technical check: rendered MP4 file exists and is non-empty
        if not episode.render_path:
            raise ValidationFailedError("Episode has no render_path")

        render_file = Path(episode.render_path)
        if not render_file.exists() or not render_file.is_file():
            raise ValidationFailedError(
                f"Rendered video file does not exist: {episode.render_path}"
            )
        if render_file.suffix.lower() != ".mp4":
            raise ValidationFailedError(
                f"Rendered video must be an .mp4 file, got '{render_file.suffix}'"
            )
        if render_file.stat().st_size == 0:
            raise ValidationFailedError("Rendered video file is empty (0 bytes)")

        # 2. Script timeline & structure check
        if not episode.script_json:
            raise ValidationFailedError("Episode is missing script_json")
        script = EpisodeScript.model_validate(episode.script_json)

        # 3. Scene completeness & duplicate check
        scenes = await SceneRepository.get_by_episode_id(db, episode_id)
        if len(scenes) != len(script.scenes):
            raise ValidationFailedError(
                f"Scene count mismatch: DB has {len(scenes)}, script has {len(script.scenes)}"
            )

        seen_prompts: set[str] = set()
        for scene in scenes:
            if scene.generation_status != SceneGenerationStatus.GENERATED.value:
                raise ValidationFailedError(
                    f"Scene {scene.sequence_number} is not in 'generated' status"
                )
            if not scene.video_path or not Path(scene.video_path).exists():
                raise ValidationFailedError(
                    f"Scene {scene.sequence_number} video file is missing"
                )
            if not scene.audio_path or not Path(scene.audio_path).exists():
                raise ValidationFailedError(
                    f"Scene {scene.sequence_number} audio file is missing"
                )

            normalized_prompt = scene.visual_prompt.strip().lower()
            if normalized_prompt in seen_prompts:
                raise ValidationFailedError(
                    f"Duplicate visual_prompt detected on scene {scene.sequence_number}"
                )
            seen_prompts.add(normalized_prompt)

            # 4. Child-safety text check
            text_to_check = f"{scene.narration_text} {scene.on_screen_text or ''}".lower()
            for term in UNSAFE_TERMS:
                if term in text_to_check.split():
                    raise ValidationFailedError(
                        f"Unsafe term '{term}' detected in scene {scene.sequence_number}"
                    )

        await EpisodeRepository.transition_status(
            db, episode, EpisodeStatus.VALIDATED
        )
        return True