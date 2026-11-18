from pathlib import Path

import pytest

from app.core import config
from app.providers.base import MediaProviderError
from app.providers.gemini_media import (
    GeminiVideoProvider,
    GeminiVoiceProvider,
    _pcm_to_wav_bytes,
)
from app.services.asset_service import resolve_video_provider, resolve_voice_provider


def test_pcm_to_wav_bytes_adds_riff_header():
    raw_pcm = b"\x00\x00" * 2400  # 0.1s of silence at 24kHz mono 16-bit
    wav_data = _pcm_to_wav_bytes(raw_pcm)
    assert wav_data.startswith(b"RIFF")
    assert len(wav_data) > len(raw_pcm)


def test_resolve_providers_selects_gemini_when_configured(monkeypatch):
    monkeypatch.setattr(config.settings, "VOICE_PROVIDER", "gemini")
    monkeypatch.setattr(config.settings, "VIDEO_PROVIDER", "gemini")

    assert isinstance(resolve_voice_provider(), GeminiVoiceProvider)
    assert isinstance(resolve_video_provider(), GeminiVideoProvider)


async def test_gemini_providers_reject_missing_api_key(tmp_path: Path):
    voice = GeminiVoiceProvider(api_key="")
    video = GeminiVideoProvider(api_key="")

    with pytest.raises(MediaProviderError, match="GEMINI_API_KEY"):
        await voice.synthesize_speech("Halo teman-teman!", tmp_path / "out.mp3")

    with pytest.raises(MediaProviderError, match="GEMINI_API_KEY"):
        await video.generate_clip("A cute 3D fox waving", 5.0, tmp_path / "out.mp4")
