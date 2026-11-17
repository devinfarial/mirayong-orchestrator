from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scene import Scene, SceneGenerationStatus
from app.schemas.script import EpisodeScript


class SceneRepository:

    @staticmethod
    async def get_by_episode_id(
        db: AsyncSession,
        episode_id: int
    ) -> list[Scene]:
        result = await db.execute(
            select(Scene)
            .where(Scene.episode_id == episode_id)
            .order_by(Scene.sequence_number.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def sync_from_script(
        db: AsyncSession,
        episode_id: int,
        script_data: dict | EpisodeScript
    ) -> list[Scene]:
        """
        Ensure Scene rows exist for the episode's script_json.
        If Scene rows already exist (e.g., on retry), return them so completed assets are preserved.
        """
        existing = await SceneRepository.get_by_episode_id(db, episode_id)
        if existing:
            return existing

        script = (
            EpisodeScript.model_validate(script_data)
            if isinstance(script_data, dict)
            else script_data
        )

        scenes: list[Scene] = []
        for s in script.scenes:
            scene = Scene(
                episode_id=episode_id,
                sequence_number=s.sequence_number,
                narration_text=s.narration_text,
                visual_prompt=s.visual_prompt,
                on_screen_text=s.on_screen_text,
                duration_seconds=s.duration_seconds,
                generation_status=SceneGenerationStatus.PENDING.value,
            )
            db.add(scene)
            scenes.append(scene)

        await db.commit()
        for scene in scenes:
            await db.refresh(scene)

        return scenes

    @staticmethod
    async def update_assets(
        db: AsyncSession,
        scene: Scene,
        video_path: str,
        audio_path: str,
        actual_cost: float,
        provider_request_id: str | None = None
    ) -> Scene:
        scene.video_path = video_path
        scene.audio_path = audio_path
        scene.actual_cost = actual_cost
        scene.provider_request_id = provider_request_id
        scene.generation_status = SceneGenerationStatus.GENERATED.value

        await db.commit()
        await db.refresh(scene)
        return scene