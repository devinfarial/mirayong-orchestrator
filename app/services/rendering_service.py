from pathlib import Path
import re
import shutil
import subprocess

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.state_machine import EpisodeStatus
from app.models.scene import Scene, SceneGenerationStatus
from app.repositories.episode_repository import EpisodeRepository
from app.repositories.scene_repository import SceneRepository

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


class RenderingError(Exception):
    """Raised when FFmpeg or rendering composition fails."""


def resolve_ffmpeg_binary() -> str:
    """Find ffmpeg on system PATH or fall back to bundled imageio-ffmpeg binary."""
    found = shutil.which(settings.FFMPEG_BINARY)
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as e:
        raise RenderingError(
            "FFmpeg binary not found on PATH and 'imageio-ffmpeg' is not installed. "
            "Run: pip install imageio-ffmpeg"
        ) from e


def probe_media_duration(ffmpeg_exe: str, file_path: Path) -> float | None:
    """Return media duration in seconds by parsing `ffmpeg -i` output."""
    result = subprocess.run(
        [ffmpeg_exe, "-i", str(file_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    match = _DURATION_RE.search(result.stderr or "")
    if not match:
        return None
    hours, minutes, seconds = (
        int(match.group(1)),
        int(match.group(2)),
        float(match.group(3)),
    )
    return hours * 3600.0 + minutes * 60.0 + seconds


def _escape_ffmpeg_filter_value(val: str) -> str:
    """Escape characters (: \\ ') for an FFmpeg filter option value."""
    return (
        val.replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )


def build_drawtext_filter(text: str | None) -> str:
    """Build an FFmpeg drawtext filter string for on_screen_text if enabled."""
    if not settings.CAPTION_ENABLED or not text or not text.strip():
        return ""

    clean_text = _escape_ffmpeg_filter_value(text.strip())
    parts: list[str] = []

    font_path = Path(settings.CAPTION_FONT_PATH)
    if not font_path.exists():
        # Fall back to Arial Bold or Arial on Windows if configured font doesn't exist
        for fallback in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
            if Path(fallback).exists():
                font_path = Path(fallback)
                break

    if font_path.exists():
        escaped_font = _escape_ffmpeg_filter_value(font_path.resolve().as_posix())
        parts.append(f"fontfile='{escaped_font}'")

    parts.extend([
        f"text='{clean_text}'",
        f"fontsize={settings.CAPTION_FONT_SIZE}",
        f"fontcolor={settings.CAPTION_FONT_COLOR}",
        f"borderw={settings.CAPTION_BORDER_WIDTH}",
        f"bordercolor={settings.CAPTION_BORDER_COLOR}",
        "shadowcolor=black@0.6",
        "shadowx=3",
        "shadowy=3",
        "x=(w-text_w)/2",
        f"y=(h*{settings.CAPTION_Y_RATIO})-(text_h/2)",
    ])

    if settings.CAPTION_BOX_ENABLED:
        parts.extend([
            "box=1",
            f"boxcolor={settings.CAPTION_BOX_COLOR}",
            f"boxborderw={settings.CAPTION_BOX_PADDING}",
        ])

    return ",drawtext=" + ":".join(parts)


class RenderingService:

    @staticmethod
    async def render_episode(
        db: AsyncSession,
        episode_id: int,
        storage_root: Path | None = None,
        mode: str | None = None,
    ) -> str:
        """
        Assemble all generated scene clips and narration audio into a 9:16 vertical MP4.
        Updates episode.render_path and transitions status to RENDERED.
        """
        episode = await EpisodeRepository.get_by_id(db, episode_id)
        if episode is None:
            raise LookupError(f"Episode with ID {episode_id} not found")

        scenes = await SceneRepository.get_by_episode_id(db, episode_id)
        if not scenes:
            raise RenderingError(f"Episode {episode_id} has no scenes to render")

        base_dir = storage_root or Path(settings.STORAGE_DIR)
        for scene in scenes:
            # Auto-relink files from storage/ if DB paths were cleared by reset-assets
            default_vid = base_dir / "generated" / f"episode_{episode.id}_scene_{scene.sequence_number}.mp4"
            default_aud = base_dir / "audio" / f"episode_{episode.id}_scene_{scene.sequence_number}.mp3"
            if (not scene.video_path or not Path(scene.video_path).exists()) and default_vid.exists():
                scene.video_path = str(default_vid)
            if (not scene.audio_path or not Path(scene.audio_path).exists()) and default_aud.exists():
                scene.audio_path = str(default_aud)
            if scene.video_path and scene.audio_path and scene.generation_status != SceneGenerationStatus.GENERATED.value:
                scene.generation_status = SceneGenerationStatus.GENERATED.value

            if scene.generation_status != SceneGenerationStatus.GENERATED.value:
                raise RenderingError(
                    f"Scene {scene.sequence_number} is not generated yet "
                    f"(status: {scene.generation_status})"
                )
            if not scene.video_path or not Path(scene.video_path).exists():
                raise RenderingError(
                    f"Missing video file for scene {scene.sequence_number}: {scene.video_path}"
                )
            if not scene.audio_path or not Path(scene.audio_path).exists():
                raise RenderingError(
                    f"Missing audio file for scene {scene.sequence_number}: {scene.audio_path}"
                )

        renders_dir = base_dir / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)
        output_path = renders_dir / f"episode_{episode.id}_final.mp4"

        render_mode = (mode or settings.RENDER_MODE).lower()
        if render_mode == "mock":
            RenderingService._render_mock(scenes, output_path)
        elif render_mode == "ffmpeg":
            RenderingService._render_ffmpeg(scenes, output_path, renders_dir)
        else:
            raise RenderingError(f"Unsupported RENDER_MODE: {render_mode}")

        episode.render_path = str(output_path)
        if episode.status != EpisodeStatus.RENDERED.value:
            episode.status = EpisodeStatus.RENDERED.value
        await db.commit()
        await db.refresh(episode)
        return str(output_path)

    @staticmethod
    def _render_mock(scenes: list[Scene], output_path: Path) -> None:
        """Deterministic mock renderer for local dry-runs and unit tests."""
        manifest_lines = ["MOCK-MP4-9x16-1080x1920"]
        for s in scenes:
            manifest_lines.append(
                f"SCENE:{s.sequence_number}|DUR:{s.duration_seconds}|"
                f"VID:{s.video_path}|AUD:{s.audio_path}|TXT:{s.on_screen_text or ''}"
            )
        output_path.write_bytes("\n".join(manifest_lines).encode("utf-8"))

    @staticmethod
    def _render_ffmpeg(
        scenes: list[Scene],
        output_path: Path,
        work_dir: Path
    ) -> None:
        """
        Normalize each scene to 1080x1920 (9:16), mux scene video + narration audio
        without cutting off either video or audio, overlay on_screen_text, and concatenate all scenes.
        """
        ffmpeg_exe = resolve_ffmpeg_binary()
        segment_paths: list[Path] = []

        try:
            for s in scenes:
                seg_path = work_dir / f"_seg_{s.episode_id}_{s.sequence_number}.mp4"
                vid_path = Path(s.video_path)
                aud_path = Path(s.audio_path)

                vid_dur = probe_media_duration(ffmpeg_exe, vid_path) or s.duration_seconds
                aud_dur = probe_media_duration(ffmpeg_exe, aud_path) or s.duration_seconds

                # Add 0.25s breathing room after the narration finishes
                target_dur = max(vid_dur, aud_dur + 0.25)

                # If audio is longer than video, smoothly stretch the video to match target_dur
                pts_chain = ""
                if vid_dur > 0 and target_dur > vid_dur:
                    stretch_ratio = target_dur / vid_dur
                    pts_chain = f"setpts={stretch_ratio:.4f}*PTS,"

                # Fall back to script_json's on_screen_text if existing DB row has on_screen_text=None
                drawtext_chain = build_drawtext_filter(s.on_screen_text)

                vf_filter = (
                    f"{pts_chain}"
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,setsar=1,fps=30"
                    f"{drawtext_chain}"
                )
                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-i", str(vid_path),
                    "-i", str(aud_path),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-vf", vf_filter,
                    "-af", "apad",
                    "-t", f"{target_dur:.3f}",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-ar", "44100",
                    "-ac", "2",
                    str(seg_path),
                ]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                segment_paths.append(seg_path)

            concat_list = work_dir / f"_concat_{scenes[0].episode_id}.txt"
            concat_list.write_text(
                "\n".join(f"file '{p.resolve().as_posix()}'" for p in segment_paths),
                encoding="utf-8",
            )

            concat_cmd = [
                ffmpeg_exe,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path),
            ]
            subprocess.run(concat_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RenderingError(f"FFmpeg rendering failed: {e.stderr or e}") from e
        except FileNotFoundError as e:
            raise RenderingError(f"FFmpeg binary not found: {e}") from e
