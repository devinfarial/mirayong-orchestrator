# Milestone 1: Foundation

## Goal
Set up the Python 3.12+ FastAPI project, PostgreSQL + Redis via Docker Compose, async SQLAlchemy ORM, Alembic migrations, and Episode CRUD endpoints.

## Java / Spring Boot to Python Mapping
- **Spring Boot (`@RestController`)** → **FastAPI (`APIRouter`)**
- **Hibernate (`@Entity`)** → **SQLAlchemy (`DeclarativeBase`, `Mapped`)**
- **Flyway / Liquibase** → **Alembic**
- **JUnit 5 + MockMvc** → **`pytest` + `httpx.AsyncClient`**

## Key Files
- [docker-compose.yml](file:///e:/Projects/mirayong-studio/docker-compose.yml) — Runs `episode-postgres` (port `5433`) and `episode-redis` (port `6379`).
- [app/core/config.py](file:///e:/Projects/mirayong-studio/app/core/config.py) — Loads `.env` settings using `pydantic-settings`.
- [app/db/base.py](file:///e:/Projects/mirayong-studio/app/db/base.py) & [app/db/session.py](file:///e:/Projects/mirayong-studio/app/db/session.py) — Async SQLAlchemy engine (`create_async_engine`) and `get_db` dependency injection.
- [app/models/episode.py](file:///e:/Projects/mirayong-studio/app/models/episode.py) — `Episode` table definition.
- [app/repositories/episode_repository.py](file:///e:/Projects/mirayong-studio/app/repositories/episode_repository.py) — Async database CRUD queries.
- [app/services/episode_service.py](file:///e:/Projects/mirayong-studio/app/services/episode_service.py) — Episode service layer.
- [app/api/episode.py](file:///e:/Projects/mirayong-studio/app/api/episode.py) — CRUD endpoints (`POST`, `GET`, `PUT`, `DELETE` under `/api/v1/episodes`).
- [tests/test_episode.py](file:///e:/Projects/mirayong-studio/tests/test_episode.py) — Integration tests using in-memory `sqlite+aiosqlite:///:memory:`.

## Commands Used
```powershell
docker compose up -d
alembic revision --autogenerate -m "create episode table"
alembic upgrade head
pytest tests/test_episode.py -v
```
