
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.episode_repository import EpisodeRepository
from app.schemas.episode import EpisodeCreate, EpisodeUpdate

class EpisodeService:

    @staticmethod
    async def create_episode(
        db: AsyncSession,
        episode_data: EpisodeCreate
    ):
        return await EpisodeRepository.create(db, episode_data)

    @staticmethod
    async def get_episode(
        db: AsyncSession,
        episode_id: int
    ):
        return await EpisodeRepository.get_by_id(db, episode_id)

    @staticmethod
    async def get_all_episodes(
        db: AsyncSession
    ):
        return await EpisodeRepository.get_all(db)

    @staticmethod
    async def update_episode(
        db: AsyncSession,
        episode_id: int,
        episode_data: EpisodeUpdate
    ):
        episode = await EpisodeRepository.get_by_id(db, episode_id)

        if episode is None:
            return None

        return await EpisodeRepository.update(
            db,
            episode,
            episode_data
        )

    @staticmethod
    async def delete_episode(
        db: AsyncSession,
        episode_id: int
    ) -> bool:
        episode = await EpisodeRepository.get_by_id(db, episode_id)

        if episode is None:
            return False

        await EpisodeRepository.delete(db, episode)
        return True
