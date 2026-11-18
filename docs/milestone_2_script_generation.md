# Milestone 2: Script Generation

## Goal
Turn a draft episode's topic into a validated, structured JSON script (`EpisodeScript`) with **Bahasa Indonesia** narration/hooks/titles and **English** 3D visual prompts, using bounded retries (`SCRIPT_MAX_ATTEMPTS = 2`).

## Key Python Concepts Learned
- **`@property`:** Exposes a method like a getter attribute (`ai_service.model_name`).
- **Exception Wrapping (`raise AIProviderError(str(e)) from e`):** Catches provider-specific errors (`AnthropicAPIError`, `GeminiAPIError`) and wraps them in a single domain exception while preserving the original stack trace.
- **Pydantic `@model_validator(mode="after")`:** Validates cross-field rules (scene `sequence_number` must be `1..N` and total duration must be between `15s` and `40s`).
- **List & String Joining (`"\n".join(lines)`):** Equivalent to Java's `String.join("\n", lines)`.

## Key Files
- [prompts/script_writer.md](file:///e:/Projects/mirayong-studio/prompts/script_writer.md) — System prompt instructing the AI to write viewer-facing fields in Bahasa Indonesia (`id`) and `visual_prompt` in English.
- [app/schemas/script.py](file:///e:/Projects/mirayong-studio/app/schemas/script.py) — `ScriptScene` and `EpisodeScript` Pydantic schemas.
- [app/services/ai_service.py](file:///e:/Projects/mirayong-studio/app/services/ai_service.py) — Unified AI adapter supporting both Anthropic Claude and Google Gemini.
- [app/services/script_service.py](file:///e:/Projects/mirayong-studio/app/services/script_service.py) — Builds the user prompt, extracts JSON, validates with `EpisodeScript`, retries with validation error feedback, and saves `script_json`.
- [migrations/versions/2157f55d8d97_add_language_to_episode.py](file:///e:/Projects/mirayong-studio/migrations/versions/2157f55d8d97_add_language_to_episode.py) — Adds `language` (`default="id"`) to the `episode` table.
- [tests/unit/test_script_service.py](file:///e:/Projects/mirayong-studio/tests/unit/test_script_service.py) — Unit tests for JSON extraction, timeline validation, and bounded retries.

## How to Test
```powershell
pytest tests/unit/test_script_service.py -v
```
Or in Swagger UI (`http://localhost:8000/docs`):
1. `POST /api/v1/episodes`
2. `POST /api/v1/episodes/{episode_id}/script`
