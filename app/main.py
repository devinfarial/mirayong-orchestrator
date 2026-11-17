
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import engine, get_db
from app.api.episode import router as episode_router
from app.api.ai import router as ai_router
from app.services.ai_service import ai_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await ai_service.close()

    


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)


app.include_router(
    episode_router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    ai_router,
    prefix=settings.API_V1_PREFIX
)


@app.get("/health")
async def health_check():
    return {
        "status": "UP",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/health/db")
async def database_health_check(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "result": result.scalar_one()
    }
