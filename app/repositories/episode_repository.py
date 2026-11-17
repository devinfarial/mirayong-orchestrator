from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.state_machine import EpisodeStatus, validate_transition
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
            target_age_band=episode_data.target_age_band,
            language=episode_data.language
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

        if "status" in update_data and update_data["status"] is not None:
            update_data["status"] = validate_transition(
                episode.status,
                update_data["status"]
            ).value

        for field, value in update_data.items():
            setattr(episode, field, value)

        await db.commit()
        await db.refresh(episode)

        return episode

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        episode: Episode,
        target_status: EpisodeStatus
    ) -> Episode:
        episode.status = validate_transition(
            episode.status,
            target_status
        ).value

        await db.commit()
        await db.refresh(episode)

        return episode

    @staticmethod
    async def save_script(
        db: AsyncSession,
        episode: Episode,
        script: dict
    ) -> Episode:
        episode.status = validate_transition(
            episode.status,
            EpisodeStatus.SCRIPT_READY
        ).value
        episode.script_json = script

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