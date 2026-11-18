from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Force .env file values to override stale OS/VS Code terminal environment variables
load_dotenv(override=True)


class Settings(BaseSettings):
    APP_NAME: str = "Episode Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str
    REDIS_URL: str

    # AI Provider
    AI_PROVIDER: str = "gemini"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    GEMINI_TTS_VOICE: str = "Zephyr"
    GEMINI_VIDEO_MODEL: str = "veo-2.0-generate-001"

    # Script generation
    DEFAULT_LANGUAGE: str = "id"
    DEFAULT_TARGET_AGE_BAND: str = "4-6"
    SCRIPT_MAX_ATTEMPTS: int = 2
    SCRIPT_MAX_TOKENS: int = 2048

    # Cost controls (USD)
    MONTHLY_BUDGET_USD: float = 25.0
    MAX_EPISODE_COST_USD: float = 10.0
    SCRIPT_ESTIMATED_COST_USD: float = 0.02
    VIDEO_COST_PER_SECOND_USD: float = 0.07
    TTS_COST_PER_1K_CHARS_USD: float = 0.30

    # Storage & Media Providers ("mock" for free local dry-runs, or "elevenlabs" / "higgsfield")
    STORAGE_DIR: str = "storage"
    VIDEO_PROVIDER: str = "mock"
    VOICE_PROVIDER: str = "mock"
    RENDER_MODE: str = "mock"
    FFMPEG_BINARY: str = "ffmpeg"

    # On-Screen Text / Caption Styling (FFmpeg drawtext)
    CAPTION_ENABLED: bool = True
    CAPTION_FONT_PATH: str = "C:/Windows/Fonts/comicbd.ttf"
    CAPTION_FONT_SIZE: int = 84
    CAPTION_FONT_COLOR: str = "white"
    CAPTION_BORDER_COLOR: str = "black"
    CAPTION_BORDER_WIDTH: int = 6
    CAPTION_Y_RATIO: float = 0.75
    CAPTION_BOX_ENABLED: bool = False
    CAPTION_BOX_COLOR: str = "black@0.45"
    CAPTION_BOX_PADDING: int = 24

    # ElevenLabs (Indonesian TTS)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "cgSgspJ2msm6clMCkdW9"  # Jessica (Young, playful, bright, expressive)
    ELEVENLABS_MODEL_ID: str = "eleven_turbo_v2_5"
    ELEVENLABS_STABILITY: float = 0.25
    ELEVENLABS_SIMILARITY_BOOST: float = 0.75
    ELEVENLABS_STYLE: float = 0.70
    ELEVENLABS_SPEED: float = 1.08

    # Higgsfield (Text-to-Video)
    HIGGSFIELD_API_KEY: str = ""
    HIGGSFIELD_BASE_URL: str = "https://api.higgsfield.ai"
    HIGGSFIELD_MODEL: str = "kling-video/v2.6/pro/text-to-video"

    # YouTube Data API v3 ("mock" for local dry-runs, or "youtube" for live upload)
    YOUTUBE_PROVIDER: str = "mock"
    YOUTUBE_ACCESS_TOKEN: str = ""
    YOUTUBE_PRIVACY_STATUS: str = "private"
    YOUTUBE_MADE_FOR_KIDS: bool = True
    YOUTUBE_CATEGORY_ID: str = "27"  # 27 = Education

    # Milestone 7: Automation & Safety Gates
    MAX_MONTHLY_EPISODES: int = 3
    BUDGET_ALERT_THRESHOLD_PCT: float = 0.80
    ALLOW_UNATTENDED_PUBLISH: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
