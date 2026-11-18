# Milestone 3: Workflow Engine, Cost Controls & Celery Worker

## Goal
Coordinate the multi-stage production pipeline (`draft -> script_ready -> assets_generated -> rendered -> validated -> publish_queued -> published`), track every stage execution in `GenerationJob`, enforce the `$25/month` budget cap before making paid calls, and support background execution with Celery + Redis.

## Key Python Concepts Learned
- **`StrEnum` (`from enum import StrEnum`):** An enum whose members are also standard `str` values (`EpisodeStatus.DRAFT == "draft"`).
- **Tuples & Unpacking (`stage, target_status = ...`):** Returning and unpacking multiple values without needing a wrapper `Pair` class.
- **Generator Expressions (`sum(s.duration_seconds for s in script.scenes)`):** Python's concise equivalent of Java's `.stream().mapToDouble(...).sum()`.
- **Bridging Sync & Async (`asyncio.run(...)`):** Running async SQLAlchemy coroutines inside synchronous Celery worker tasks.

## Key Files
- [app/core/state_machine.py](file:///e:/Projects/mirayong-studio/app/core/state_machine.py) — `EpisodeStatus` enum, `ALLOWED_TRANSITIONS`, `can_transition()`, and `validate_transition()`.
- [app/models/generation_job.py](file:///e:/Projects/mirayong-studio/app/models/generation_job.py) — `GenerationJob`, `JobStage`, and `JobStatus` models.
- [app/repositories/job_repository.py](file:///e:/Projects/mirayong-studio/app/repositories/job_repository.py) — Job lifecycle methods (`mark_running`, `mark_succeeded`, `mark_failed`, `get_monthly_spend`).
- [app/core/cost_manager.py](file:///e:/Projects/mirayong-studio/app/core/cost_manager.py) — `CostManager` pre-stage cost estimator and `$25.00` monthly cap guard (`BudgetExceededError`).
- [app/core/orchestration.py](file:///e:/Projects/mirayong-studio/app/core/orchestration.py) — `WorkflowOrchestrator` (`run_next_stage` and `retry_failed_episode`).
- [app/workers/celery_app.py](file:///e:/Projects/mirayong-studio/app/workers/celery_app.py) & [app/workers/tasks.py](file:///e:/Projects/mirayong-studio/app/workers/tasks.py) — Celery + Redis worker integration.
- [tests/test_state_machine.py](file:///e:/Projects/mirayong-studio/tests/test_state_machine.py), [tests/unit/test_cost_manager.py](file:///e:/Projects/mirayong-studio/tests/unit/test_cost_manager.py), [tests/unit/test_orchestration.py](file:///e:/Projects/mirayong-studio/tests/unit/test_orchestration.py) — Unit & integration tests.

## Commands Used
```powershell
alembic revision --autogenerate -m "create generation_job table"
alembic upgrade head
pytest tests/test_state_machine.py tests/unit/test_cost_manager.py tests/unit/test_orchestration.py -v
```
