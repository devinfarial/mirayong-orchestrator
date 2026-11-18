from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cost_manager import CostManager
from app.db.session import get_db
from app.repositories.job_repository import JobRepository
from app.schemas.job import GenerationJobResponse

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.get("/report/monthly")
async def get_monthly_cost_report(
    db: AsyncSession = Depends(get_db)
):
    return await CostManager.get_monthly_report(db)


@router.get(
    "/{job_id}",
    response_model=GenerationJobResponse
)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    job = await JobRepository.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    return job
