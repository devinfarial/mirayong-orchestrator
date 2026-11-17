
from anthropic import APIError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.episode import EpisodeCreate, EpisodeResponse, EpisodeUpdate
from app.services.episode_service import EpisodeService
from app.services.script_service import (
    ScriptGenerationError,
    ScriptNotAllowedError,
    ScriptService,
)


router = APIRouter(
    prefix="/episodes",
    tags=["Episodes"]
)


@router.post(
    "",
    response_model=EpisodeResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_episode(
    episode_data: EpisodeCreate,
    db: AsyncSession = Depends(get_db)
):
    return await EpisodeService.create_episode(db, episode_data)


@router.get(
    "",
    response_model=list[EpisodeResponse]
)
async def get_all_episodes(
    db: AsyncSession = Depends(get_db)
):
    return await EpisodeService.get_all_episodes(db)


@router.get(
    "/{episode_id}",
    response_model=EpisodeResponse
)
async def get_episode(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    episode = await EpisodeService.get_episode(db, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )

    return episode

@router.post(
    "/{episode_id}/script",
    response_model=EpisodeResponse
)
async def generate_episode_script(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        episode = await ScriptService.generate_script(db, episode_id)

    except ScriptNotAllowedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    except ScriptGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": type(e).__name__, "message": str(e)}
        )

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )

    return episode


@router.put(
    "/{episode_id}",
    response_model=EpisodeResponse
)
async def update_episode(
    episode_id: int,
    episode_data: EpisodeUpdate,
    db: AsyncSession = Depends(get_db)
):
    episode = await EpisodeService.update_episode(
        db,
        episode_id,
        episode_data
    )

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )

    return episode

@router.delete(
    "/{episode_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_episode(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    deleted = await EpisodeService.delete_episode(db, episode_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )

    return None
