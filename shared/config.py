import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    google_credentials_file_path: str = ""

    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    sarvam_api_key: str = ""
    artifacts_dir: str = "artifacts"
    sql_database_url: str = ""

    # Voice pipeline — swap model/voice here without touching agent.py
    stt_model: str = "latest_long"
    stt_location: str = "global"
    tts_voice: str = "en-US-Chirp3-HD-Charon"


settings = Settings()

# Inject into os.environ so third-party libs (e.g. langchain) can find them
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
