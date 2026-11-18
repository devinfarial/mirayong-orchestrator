# Milestone 5: Rendering and Validation

## Goal
Assemble all generated scene clips and Indonesian voiceover tracks into a single 9:16 (`1080x1920`) vertical `.mp4` in `storage/renders/`, and run automated technical & child-safety validation checks before allowing upload.

## Key Files
- [app/services/rendering_service.py](file:///e:/Projects/mirayong-studio/app/services/rendering_service.py) — `RenderingService.render_episode`:
  - Verifies every scene is `generated` and its video/audio files exist on disk.
  - Supports `RENDER_MODE="mock"` (deterministic dry-run `.mp4`) and `RENDER_MODE="ffmpeg"` (scales/pads to `1080x1920` 30fps, muxes H.264 + AAC audio, and concatenates scenes via FFmpeg).
  - Saves `episode.render_path` and transitions status to `rendered`.
- [app/services/validation_service.py](file:///e:/Projects/mirayong-studio/app/services/validation_service.py) — `ValidationService.validate_episode`:
  - Verifies `render_path` exists, ends in `.mp4`, and is non-empty (`st_size > 0`).
  - Re-validates `script_json` timeline bounds (`15s`–`40s`, `3`–`6` scenes).
  - Checks for accidental duplicate `visual_prompt`s across scenes.
  - Checks narration and on-screen text against child-safety blocklist (`UNSAFE_TERMS`).
  - Transitions status from `rendered` to `validated`.
- [tests/unit/test_rendering_and_validation.py](file:///e:/Projects/mirayong-studio/tests/unit/test_rendering_and_validation.py) — Pipeline test covering `script -> assets -> render -> validate`.

## Commands Used
```powershell
alembic revision --autogenerate -m "add render_path and youtube_video_id to episode"
alembic upgrade head
pytest tests/unit/test_rendering_and_validation.py -v
```
