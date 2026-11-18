import asyncio
import base64
import io
from pathlib import Path
import uuid
import wave

from google import genai
from google.genai import types
import httpx

from app.core.config import settings
from app.providers.base import AssetResult, MediaProviderError


def _pcm_to_wav_bytes(
    pcm_data: bytes,
    sample_rate: int = 24000,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Wrap raw 16-bit 24kHz mono PCM audio from Gemini TTS into a playable WAV container."""
    if pcm_data.startswith(b"RIFF"):
        return pcm_data

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buffer.getvalue()


class GeminiVoiceProvider:
    """Adapter for Google Gemini Text-to-Speech (gemini-2.5-flash-preview-tts)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY

    async def synthesize_speech(
        self,
        text: str,
        output_path: Path,
        language: str = "id"
    ) -> AssetResult:
        if not self.api_key:
            raise MediaProviderError("GEMINI_API_KEY is not configured for Gemini TTS")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        client = genai.Client(
            api_key=self.api_key,
            http_options={"api_version": "v1beta"},
        )

        try:
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_TTS_MODEL,
                contents=(
                    "Speak in Bahasa Indonesia with a super cheerful, energetic, playful, "
                    "and enthusiastic young female kids-show host voice (high energy, warm, "
                    f"bouncy intonation): {text}"
                ),
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=settings.GEMINI_TTS_VOICE,
                            )
                        )
                    ),
                ),
            )
        except Exception as e:
            raise MediaProviderError(f"Gemini TTS error: {e}") from e
        finally:
            await client.aio.aclose()

        try:
            inline_data = response.candidates[0].content.parts[0].inline_data
            raw_audio = inline_data.data
            if isinstance(raw_audio, str):
                raw_audio = base64.b64decode(raw_audio)
        except (AttributeError, IndexError, TypeError) as e:
            raise MediaProviderError(
                "Gemini TTS response did not contain audio inline_data"
            ) from e

        wav_bytes = _pcm_to_wav_bytes(raw_audio)
        output_path.write_bytes(wav_bytes)

        cost = round((len(text) / 1000.0) * settings.TTS_COST_PER_1K_CHARS_USD, 4)
        return AssetResult(
            file_path=str(output_path),
            provider_request_id=f"gemini-tts-{uuid.uuid4().hex[:8]}",
            actual_cost=cost,
        )


class GeminiVideoProvider:
    """Adapter for Google Veo text-to-video generation via the Gemini API."""

    def __init__(self, api_key: str | None = None, poll_interval_seconds: float = 5.0):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.poll_interval_seconds = poll_interval_seconds

    async def generate_clip(
        self,
        visual_prompt: str,
        duration_seconds: float,
        output_path: Path
    ) -> AssetResult:
        if not self.api_key:
            raise MediaProviderError("GEMINI_API_KEY is not configured for Gemini Veo")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        client = genai.Client(
            api_key=self.api_key,
            http_options={"api_version": "v1beta"},
        )

        try:
            operation = await client.aio.models.generate_videos(
                model=settings.GEMINI_VIDEO_MODEL,
                prompt=f"{visual_prompt}. Do not render any text or letters in the frame.",
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",
                    number_of_videos=1,
                ),
            )

            while not operation.done:
                await asyncio.sleep(self.poll_interval_seconds)
                operation = await client.aio.operations.get(operation)

            generated_videos = getattr(operation.response, "generated_videos", None)
            if not generated_videos:
                raise MediaProviderError("Gemini Veo operation completed with no generated_videos")

            video_obj = generated_videos[0].video
            video_bytes = getattr(video_obj, "video_bytes", None)

            if not video_bytes and getattr(video_obj, "uri", None):
                async with httpx.AsyncClient(timeout=120.0) as http_client:
                    resp = await http_client.get(
                        video_obj.uri,
                        headers={"x-goog-api-key": self.api_key},
                        follow_redirects=True,
                    )
                    resp.raise_for_status()
                    video_bytes = resp.content

            if not video_bytes:
                raise MediaProviderError("Gemini Veo response contained neither video_bytes nor a downloadable URI")

            if isinstance(video_bytes, str):
                video_bytes = base64.b64decode(video_bytes)

            output_path.write_bytes(video_bytes)
            op_name = getattr(operation, "name", None) or f"veo-{uuid.uuid4().hex[:8]}"
            cost = round(duration_seconds * settings.VIDEO_COST_PER_SECOND_USD, 4)

            return AssetResult(
                file_path=str(output_path),
                provider_request_id=str(op_name),
                actual_cost=cost,
            )
        except MediaProviderError:
            raise
        except Exception as e:
            raise MediaProviderError(f"Gemini Veo error: {e}") from e
        finally:
            await client.aio.aclose()
