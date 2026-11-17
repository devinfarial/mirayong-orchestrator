from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class MediaProviderError(Exception):
    """Raised when an external video or voice provider fails."""


@dataclass
class AssetResult:
    file_path: str
    provider_request_id: str
    actual_cost: float


class VoiceProvider(Protocol):
    async def synthesize_speech(
        self,
        text: str,
        output_path: Path,
        language: str = "id"
    ) -> AssetResult:
        ...


class VideoProvider(Protocol):
    async def generate_clip(
        self,
        visual_prompt: str,
        duration_seconds: float,
        output_path: Path
    ) -> AssetResult:
        ...