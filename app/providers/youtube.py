from dataclasses import dataclass
import json
from pathlib import Path
import uuid

import httpx

from app.core.config import settings


class YouTubePublishError(Exception):
    """Raised when uploading a video to YouTube fails."""


@dataclass
class YouTubeUploadResult:
    video_id: str
    video_url: str


class YouTubeProvider:
    """Adapter for YouTube Data API v3 video upload."""

    def __init__(self, mode: str | None = None):
        self.mode = (mode or settings.YOUTUBE_PROVIDER).lower()

    @staticmethod
    def build_metadata(
        title: str,
        description: str,
        language: str = "id",
        tags: list[str] | None = None,
    ) -> dict:
        short_title = title if "#Shorts" in title else f"{title} #Shorts"
        return {
            "snippet": {
                "title": short_title[:100],
                "description": description,
                "tags": tags or ["Shorts", "EdukasiAnak", "BelajarAnak", "Animasi3D"],
                "categoryId": settings.YOUTUBE_CATEGORY_ID,
                "defaultLanguage": language,
                "defaultAudioLanguage": language,
            },
            "status": {
                "privacyStatus": settings.YOUTUBE_PRIVACY_STATUS,
                "selfDeclaredMadeForKids": settings.YOUTUBE_MADE_FOR_KIDS,
            },
        }

    async def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        language: str = "id",
    ) -> YouTubeUploadResult:
        if not video_path.exists():
            raise YouTubePublishError(f"Video file not found: {video_path}")

        metadata = self.build_metadata(
            title=title,
            description=description,
            language=language,
        )

        if self.mode == "mock":
            fake_id = f"yt_mock_{uuid.uuid4().hex[:10]}"
            return YouTubeUploadResult(
                video_id=fake_id,
                video_url=f"https://youtube.com/shorts/{fake_id}",
            )

        if not settings.YOUTUBE_ACCESS_TOKEN:
            raise YouTubePublishError("YOUTUBE_ACCESS_TOKEN is not configured")

        upload_url = (
            "https://www.googleapis.com/upload/youtube/v3/videos"
            "?uploadType=multipart&part=snippet,status"
        )
        headers = {
            "Authorization": f"Bearer {settings.YOUTUBE_ACCESS_TOKEN}",
        }
        files = {
            "metadata": (
                "metadata.json",
                json.dumps(metadata).encode("utf-8"),
                "application/json; charset=UTF-8",
            ),
            "file": (
                video_path.name,
                video_path.read_bytes(),
                "video/mp4",
            ),
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(upload_url, headers=headers, files=files)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            raise YouTubePublishError(f"YouTube upload failed: {e}") from e

        video_id = data.get("id")
        if not video_id:
            raise YouTubePublishError("YouTube API response did not include video 'id'")

        return YouTubeUploadResult(
            video_id=video_id,
            video_url=f"https://youtube.com/shorts/{video_id}",
        )
