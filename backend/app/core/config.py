from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://hadith:hadith@db:5432/hadith_db"

    # OpenAI API
    OPENAI_API_KEY: SecretStr = SecretStr("")
    OPENAI_TEXT_MODEL: str = "gpt-5-mini"

    # Sunnah.com API
    SUNNAH_API_KEY: str = ""
    SUNNAH_API_BASE: str = "https://api.sunnah.com/v1"

    # App
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Hadith Reclassifier"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
    )


settings = Settings()
