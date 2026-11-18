# Milestone 4: Video and Voice Assets

## Goal
Generate per-scene Bahasa Indonesia narration audio (`.mp3` via ElevenLabs) and 3D animated scene video clips (`.mp4` via Higgsfield), store them in `storage/audio/` and `storage/generated/`, and track each scene in the `scene` table so retries never re-purchase already completed scenes.

## Key Python Concepts Learned
- **`@dataclass` (`from dataclasses import dataclass`):** Equivalent to a Java `record` (`AssetResult`).
- **`Protocol` (`from typing import Protocol`):** Equivalent to a Java `interface` (`VideoProvider`, `VoiceProvider`) using structural subtyping.
- **`pathlib.Path` `/` operator:** Cross-platform path joining (`base_dir / "audio" / f"episode_{id}.mp3"`).
- **Python Default Argument Binding Rule:** Default function arguments (`def fn(ai=ai_service)`) are evaluated once when the module is imported, so tests should mock methods on the instance (`ai_service.generate_response`) rather than reassigning the module attribute.

## Key Files
- [app/models/scene.py](file:///e:/Projects/mirayong-studio/app/models/scene.py) & [app/repositories/scene_repository.py](file:///e:/Projects/mirayong-studio/app/repositories/scene_repository.py) — Stores per-scene `video_path`, `audio_path`, `generation_status`, `provider_request_id`, and `actual_cost`.
- [app/providers/base.py](file:///e:/Projects/mirayong-studio/app/providers/base.py) — `AssetResult`, `VoiceProvider`, and `VideoProvider` protocols.
- [app/providers/elevenlabs.py](file:///e:/Projects/mirayong-studio/app/providers/elevenlabs.py) — ElevenLabs Multilingual v2 Indonesian TTS adapter (supports `"mock"` and `"elevenlabs"` modes).
- [app/providers/higgsfield.py](file:///e:/Projects/mirayong-studio/app/providers/higgsfield.py) — Higgsfield 9:16 3D video adapter (supports `"mock"` and `"higgsfield"` modes).
- [app/services/asset_service.py](file:///e:/Projects/mirayong-studio/app/services/asset_service.py) — Orchestrates scene asset generation with per-scene idempotency.
- [tests/test_asset_service.py](file:///e:/Projects/mirayong-studio/tests/test_asset_service.py) — End-to-end asset generation and idempotency tests.

## Commands Used
```powershell
alembic revision --autogenerate -m "create scene table"
alembic upgrade head
pytest tests/test_asset_service.py -v
```
