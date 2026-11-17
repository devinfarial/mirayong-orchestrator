from pathlib import Path
import uuid

import httpx

from app.core.config import settings
from app.providers.base import AssetResult, MediaProviderError


class ElevenLabsProvider:
    """Adapter for ElevenLabs Multilingual v2 Text-to-Speech (supports Bahasa Indonesia)."""

    def __init__(self, mode: str | None = None):
        self.mode = (mode or settings.VOICE_PROVIDER).lower()

    async def synthesize_speech(
        self,
        text: str,
        output_path: Path,
        language: str = "id"
    ) -> AssetResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cost = round((len(text) / 1000.0) * settings.TTS_COST_PER_1K_CHARS_USD, 4)

        if self.mode == "mock":
            # Free local dry-run mode: write placeholder audio bytes
            output_path.write_bytes(b"ID3-MOCK-INDONESIAN-AUDIO:" + text.encode("utf-8"))
            return AssetResult(
                file_path=str(output_path),
                provider_request_id=f"mock-tts-{uuid.uuid4().hex[:8]}",
                actual_cost=0.0,
            )

        if not settings.ELEVENLABS_API_KEY:
            raise MediaProviderError("ELEVENLABS_API_KEY is not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": settings.ELEVENLABS_MODEL_ID,
            "language_code": language,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise MediaProviderError(f"ElevenLabs API error: {e}") from e

        output_path.write_bytes(response.content)
        request_id = response.headers.get("request-id", f"el-{uuid.uuid4().hex[:8]}")

        return AssetResult(
            file_path=str(output_path),
            provider_request_id=request_id,
            actual_cost=cost,
        )