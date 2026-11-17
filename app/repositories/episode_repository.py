
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.episode import Episode
from app.schemas.episode import EpisodeCreate, EpisodeUpdate

class EpisodeRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        episode_data: EpisodeCreate
    ) -> Episode:
        episode = Episode(
            title=episode_data.title,
            description=episode_data.description,
            topic=episode_data.topic,
            target_age_band=episode_data.target_age_band
        )

        db.add(episode)
        await db.commit()
        await db.refresh(episode)

        return episode

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        episode_id: int
    ) -> Episode | None:
        result = await db.execute(
            select(Episode).where(Episode.id == episode_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession
    ) -> list[Episode]:
        result = await db.execute(
            select(Episode).order_by(Episode.id.desc())
        )

        return list(result.scalars().all())


    @staticmethod
    async def update(
        db: AsyncSession,
        episode: Episode,
        episode_data: EpisodeUpdate
    ) -> Episode:
        update_data = episode_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(episode, field, value)

        await db.commit()
        await db.refresh(episode)

        return episode


    @staticmethod
    async def save_script(
        db: AsyncSession,
        episode: Episode,
        script: dict
    ) -> Episode:
        episode.script_json = script
        episode.status = "script_ready"

        await db.commit()
        await db.refresh(episode)

        return episode


    @staticmethod
    async def delete(
        db: AsyncSession,
        episode: Episode
    ) -> None:
        await db.delete(episode)
        await db.commit()
