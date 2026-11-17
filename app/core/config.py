from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Script generation
    DEFAULT_LANGUAGE: str = "id"
    DEFAULT_TARGET_AGE_BAND: str = "4-6"
    SCRIPT_MAX_ATTEMPTS: int = 2
    SCRIPT_MAX_TOKENS: int = 2048

    # Cost controls (USD)
    MONTHLY_BUDGET_USD: float = 25.0
    MAX_EPISODE_COST_USD: float = 10.0
    SCRIPT_ESTIMATED_COST_USD: float = 0.02
    VIDEO_COST_PER_SECOND_USD: float = 0.15
    TTS_COST_PER_1K_CHARS_USD: float = 0.30

    # Storage & Media Providers ("mock" for free local dry-runs, or "elevenlabs" / "higgsfield")
    STORAGE_DIR: str = "storage"
    VIDEO_PROVIDER: str = "mock"
    VOICE_PROVIDER: str = "mock"

    # ElevenLabs (Indonesian TTS)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"

    # Higgsfield (Text-to-Video)
    HIGGSFIELD_API_KEY: str = ""
    HIGGSFIELD_API_URL: str = "https://api.higgsfield.ai/v1/generations"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
