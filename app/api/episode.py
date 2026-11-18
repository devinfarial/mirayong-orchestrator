from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cost_manager import BudgetExceededError
from app.core.orchestration import WorkflowError, WorkflowOrchestrator
from app.db.session import get_db
from app.providers.base import MediaProviderError
from app.providers.youtube import YouTubePublishError
from app.repositories.job_repository import JobRepository
from app.repositories.scene_repository import SceneRepository
from app.schemas.episode import (
    EpisodeCreate,
    EpisodeResponse,
    EpisodeStatusResponse,
    EpisodeUpdate,
)
from app.schemas.job import GenerationJobResponse
from app.schemas.scene import SceneResponse
from app.services.ai_service import AIProviderError
from app.services.asset_service import AssetGenerationError
from app.services.episode_service import EpisodeService
from app.services.rendering_service import RenderingError
from app.services.script_service import (
    ScriptGenerationError,
    ScriptNotAllowedError,
    ScriptService,
)
from app.services.validation_service import ValidationFailedError

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

    except AIProviderError as e:
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


@router.post(
    "/{episode_id}/generate",
    response_model=GenerationJobResponse
)
async def generate_next_stage(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await WorkflowOrchestrator.run_next_stage(db, episode_id)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BudgetExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    except (
        ScriptGenerationError,
        AIProviderError,
        AssetGenerationError,
        MediaProviderError,
        RenderingError,
        ValidationFailedError,
        YouTubePublishError,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.post(
    "/{episode_id}/run-pipeline",
    response_model=list[GenerationJobResponse]
)
async def run_episode_pipeline(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await WorkflowOrchestrator.run_pipeline(db, episode_id)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BudgetExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    except (
        ScriptGenerationError,
        AIProviderError,
        AssetGenerationError,
        MediaProviderError,
        RenderingError,
        ValidationFailedError,
        YouTubePublishError,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.get(
    "/{episode_id}/status",
    response_model=EpisodeStatusResponse
)
async def get_episode_status(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    episode = await EpisodeService.get_episode(db, episode_id)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )
    jobs = await JobRepository.get_by_episode_id(db, episode_id)
    return EpisodeStatusResponse(
        episode_id=episode.id,
        status=episode.status,
        jobs=jobs
    )


@router.get(
    "/{episode_id}/scenes",
    response_model=list[SceneResponse]
)
async def get_episode_scenes(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    episode = await EpisodeService.get_episode(db, episode_id)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )
    return await SceneRepository.get_by_episode_id(db, episode_id)


@router.post(
    "/{episode_id}/reset-assets",
    response_model=EpisodeResponse
)
async def reset_episode_assets(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Revert an episode back to 'script_ready' and reset its scenes to 'pending' so assets can be regenerated."""
    episode = await EpisodeService.get_episode(db, episode_id)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with ID {episode_id} not found"
        )
    if not episode.script_json:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Episode does not have a script yet"
        )

    await SceneRepository.reset_by_episode_id(db, episode_id)
    episode.status = "script_ready"
    episode.render_path = None
    await db.commit()
    await db.refresh(episode)
    return episode


@router.post(
    "/{episode_id}/render",
    response_model=EpisodeResponse
)
async def render_episode_now(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Render (or re-render) an episode's scene video + audio files into the final 9:16 MP4."""
    from app.services.rendering_service import RenderingService
    try:
        await RenderingService.render_episode(db, episode_id)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RenderingError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    return await EpisodeService.get_episode(db, episode_id)


@router.post(
    "/{episode_id}/retry",
    response_model=GenerationJobResponse
)
async def retry_episode(
    episode_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await WorkflowOrchestrator.retry_failed_episode(db, episode_id)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BudgetExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    except (
        ScriptGenerationError,
        AIProviderError,
        AssetGenerationError,
        MediaProviderError,
        RenderingError,
        ValidationFailedError,
        YouTubePublishError,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


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
