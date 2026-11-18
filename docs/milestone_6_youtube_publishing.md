# Milestone 6: YouTube Publishing

## Goal
Upload a `validated` episode's rendered `.mp4` to YouTube Shorts via the YouTube Data API v3 with Bahasa Indonesia metadata (`defaultLanguage="id"`, `defaultAudioLanguage="id"`), `selfDeclaredMadeForKids=True`, and idempotency so retries never create duplicate uploads.

## Key Files
- [app/providers/youtube.py](file:///e:/Projects/mirayong-studio/app/providers/youtube.py) — `YouTubeProvider`:
  - `build_metadata()`: Appends `#Shorts` to the title, sets `categoryId="27"` (Education), `defaultLanguage="id"`, `privacyStatus`, and `selfDeclaredMadeForKids=True`.
  - `upload_video()`: Supports `YOUTUBE_PROVIDER="mock"` (returns `yt_mock_<id>`) and `YOUTUBE_PROVIDER="youtube"` (multipart upload to `https://www.googleapis.com/upload/youtube/v3/videos`).
- [app/services/publishing_service.py](file:///e:/Projects/mirayong-studio/app/services/publishing_service.py) — `PublishingService.publish_episode`:
  - Idempotency check: if `episode.youtube_video_id` is already populated, returns it immediately without re-uploading.
  - Transitions `validated -> publish_queued -> published` and persists `youtube_video_id`.
- [tests/unit/test_publishing_service.py](file:///e:/Projects/mirayong-studio/tests/unit/test_publishing_service.py) — Tests metadata rules and the full 5-stage pipeline from `draft` to `published`.

## Commands Used
```powershell
pytest tests/unit/test_publishing_service.py -v
```
