# Milestone 7: Controlled Automation & Monthly Cost Reporting

## Goal
Add monthly budget reporting with threshold alerts (`80%` of the `$25.00` cap) and a one-click pipeline autopilot (`POST /api/v1/episodes/{id}/run-pipeline`) that stops at `validated` for human review unless `ALLOW_UNATTENDED_PUBLISH=True`.

## Key Files
- [app/core/cost_manager.py](file:///e:/Projects/mirayong-studio/app/core/cost_manager.py) — `CostManager.get_monthly_report()` calculates monthly spend, remaining budget, utilization percentage, and emits `BUDGET_THRESHOLD_WARNING` when spend crosses `BUDGET_ALERT_THRESHOLD_PCT` (`0.80`).
- [app/api/job.py](file:///e:/Projects/mirayong-studio/app/api/job.py) — Exposes `GET /api/v1/jobs/report/monthly`.
- [app/core/orchestration.py](file:///e:/Projects/mirayong-studio/app/core/orchestration.py) — `WorkflowOrchestrator.run_pipeline()` runs all stages sequentially and pauses at `validated` when `ALLOW_UNATTENDED_PUBLISH=False`.
- [app/api/episode.py](file:///e:/Projects/mirayong-studio/app/api/episode.py) — Exposes `POST /api/v1/episodes/{episode_id}/run-pipeline`.
- [tests/unit/test_milestone7_automation.py](file:///e:/Projects/mirayong-studio/tests/unit/test_milestone7_automation.py) — Tests monthly budget alert thresholds and the human-review gate on `run-pipeline`.

## Commands Used
```powershell
pytest tests/unit/test_milestone7_automation.py -v
```
