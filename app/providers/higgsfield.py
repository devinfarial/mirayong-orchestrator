import asyncio
import json
from pathlib import Path
import uuid

import httpx

from app.core.config import settings
from app.providers.base import AssetResult, MediaProviderError

TERMINAL_STATUSES = {"completed", "failed", "nsfw", "canceled"}


class HiggsfieldProvider:
    """Adapter for Higgsfield text-to-video generation."""

    def __init__(
        self,
        mode: str | None = None,
        model: str | None = None,
    ):
        self.mode = (mode or settings.VIDEO_PROVIDER).lower()
        self.model = model or settings.HIGGSFIELD_MODEL

    async def generate_clip(
        self,
        visual_prompt: str,
        duration_seconds: float,
        output_path: Path,
    ) -> AssetResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Higgsfield Kling models accept 5 or 10 second durations; use 5s for scenes up to 7s
        # (RenderingService smoothly stretches 5s video if narration is 6s, saving 50% on clip cost)
        clip_duration = 5 if duration_seconds <= 7 else 10
        cost = round(clip_duration * settings.VIDEO_COST_PER_SECOND_USD, 4)

        if self.mode == "mock":
            # Keep existing real video file if user manually dropped a clip (e.g. from Google Flow)
            if not output_path.exists() or output_path.stat().st_size < 1024:
                output_path.write_bytes(b"MOCK-MP4-CLIP:" + visual_prompt.encode("utf-8"))
            return AssetResult(
                file_path=str(output_path),
                provider_request_id=f"mock-vid-{uuid.uuid4().hex[:8]}",
                actual_cost=0.0,
            )

        api_key = settings.HIGGSFIELD_API_KEY.strip().removeprefix("your_key_id:")
        if not api_key:
            raise MediaProviderError("HIGGSFIELD_API_KEY is not configured")

        model_path = self.model.lstrip("/")
        if model_path in (
            "kling-video/v2.5-turbo/text-to-video",
            "kling-video/v2.5-turbo/standard/text-to-video",
            "kling-video/v2.5-turbo/pro/text-to-video",
            "kling-video/v2.6/text-to-video",
        ):
            model_path = "kling-video/v2.6/pro/text-to-video"

        url = f"{settings.HIGGSFIELD_BASE_URL.rstrip('/')}/{model_path}"
        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": f"{visual_prompt}. Do not render any text or letters in the frame.",
            "duration": clip_duration,
            "aspect_ratio": "9:16",
            "sound": "off",
        }

        pending_meta_path = output_path.with_suffix(".mp4.req.json")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Resume an in-flight Higgsfield request if a previous run timed out mid-poll
                if pending_meta_path.exists():
                    saved_meta = json.loads(pending_meta_path.read_text(encoding="utf-8"))
                    request_id = saved_meta["request_id"]
                    status_url = saved_meta["status_url"]
                else:
                    # 1. Submit async generation job
                    submit_resp = await client.post(url, headers=headers, json=payload)
                    submit_resp.raise_for_status()
                    job_data = submit_resp.json()

                    request_id = job_data.get("request_id", f"hf-{uuid.uuid4().hex[:8]}")
                    status_url = job_data.get(
                        "status_url",
                        f"{settings.HIGGSFIELD_BASE_URL.rstrip('/')}/requests/{request_id}/status",
                    )
                    pending_meta_path.write_text(
                        json.dumps({"request_id": request_id, "status_url": status_url}),
                        encoding="utf-8",
                    )

                # 2. Poll status_url until completed (up to 10 minutes: 120 * 5s)
                video_url = await self._poll_for_video_url(
                    client, status_url, headers, max_polls=120, poll_interval=5.0
                )

                # 3. Download the finished MP4
                video_resp = await client.get(video_url, timeout=120.0)
                video_resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text.strip()
            key_hint = f"{api_key[:8]}..." if api_key else "empty"
            raise MediaProviderError(
                f"Higgsfield API error ({e.response.status_code}, key={key_hint}): {detail or e}"
            ) from e
        except httpx.HTTPError as e:
            raise MediaProviderError(f"Higgsfield API error: {e}") from e

        output_path.write_bytes(video_resp.content)
        pending_meta_path.unlink(missing_ok=True)

        return AssetResult(
            file_path=str(output_path),
            provider_request_id=request_id,
            actual_cost=cost,
        )

    @staticmethod
    async def _poll_for_video_url(
        client: httpx.AsyncClient,
        status_url: str,
        headers: dict[str, str],
        max_polls: int = 120,
        poll_interval: float = 5.0,
    ) -> str:
        for _ in range(max_polls):
            resp = await client.get(status_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            status = data.get("status")
            if status in TERMINAL_STATUSES:
                if status != "completed":
                    error_msg = data.get("error") or f"Job ended with status '{status}'"
                    raise MediaProviderError(f"Higgsfield generation failed: {error_msg}")

                video_url = (
                    data.get("video", {}).get("url")
                    or data.get("payload", {}).get("video", {}).get("url")
                    or data.get("video_url")
                )
                if not video_url:
                    raise MediaProviderError("Higgsfield completed response missing video URL")
                return video_url

            await asyncio.sleep(poll_interval)

        raise MediaProviderError("Timed out waiting for Higgsfield video generation")
