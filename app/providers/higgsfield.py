from pathlib import Path
import uuid

import httpx

from app.core.config import settings
from app.providers.base import AssetResult, MediaProviderError


class HiggsfieldProvider:
    """Adapter for Higgsfield text-to-video generation."""

    def __init__(self, mode: str | None = None):
        self.mode = (mode or settings.VIDEO_PROVIDER).lower()

    async def generate_clip(
        self,
        visual_prompt: str,
        duration_seconds: float,
        output_path: Path
    ) -> AssetResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cost = round(duration_seconds * settings.VIDEO_COST_PER_SECOND_USD, 4)

        if self.mode == "mock":
            # Free local dry-run mode: write placeholder MP4 bytes
            output_path.write_bytes(b"MOCK-MP4-CLIP:" + visual_prompt.encode("utf-8"))
            return AssetResult(
                file_path=str(output_path),
                provider_request_id=f"mock-vid-{uuid.uuid4().hex[:8]}",
                actual_cost=0.0,
            )

        if not settings.HIGGSFIELD_API_KEY:
            raise MediaProviderError("HIGGSFIELD_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {settings.HIGGSFIELD_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": f"{visual_prompt}. Do not render any text or letters in the frame.",
            "duration": duration_seconds,
            "aspect_ratio": "9:16",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    settings.HIGGSFIELD_API_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                request_id = data.get("id", f"hf-{uuid.uuid4().hex[:8]}")
                video_url = data.get("video_url")
                if not video_url:
                    raise MediaProviderError("Higgsfield response missing 'video_url'")

                video_resp = await client.get(video_url)
                video_resp.raise_for_status()
        except httpx.HTTPError as e:
            raise MediaProviderError(f"Higgsfield API error: {e}") from e

        output_path.write_bytes(video_resp.content)

        return AssetResult(
            file_path=str(output_path),
            provider_request_id=request_id,
            actual_cost=cost,
        )