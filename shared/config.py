import os
import tempfile

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    google_credentials_file_path: str = ""
    google_credentials_json: str = ""

    # ADR: Workaround in-case things fail at the infra side of things. I ain't a great devops but this should work in-case i dont get the file in :)
    # TODO: Remove this if i'm able to mount the credentials file properly.
    @model_validator(mode="after")
    def write_google_credentials(self) -> "Settings":
        if self.google_credentials_json and not self.google_credentials_file_path:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            tmp.write(self.google_credentials_json)
            tmp.close()
            self.google_credentials_file_path = tmp.name
        return self

    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    sarvam_api_key: str = ""
    artifacts_dir: str = "artifacts"
    sql_database_url: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]

    # Voice pipeline — swap model/voice here without touching agent.py
    stt_model: str = "latest_long"
    stt_location: str = "global"
    tts_voice: str = "en-US-Chirp3-HD-Charon"


settings = Settings()

# Inject into os.environ so third-party libs (e.g. langchain) can find them
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
