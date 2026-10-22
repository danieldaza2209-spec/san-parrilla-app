import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for finding .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./san_parrilla.db"
    APP_NAME: str = "San Parrilla API"
    DEBUG: bool = True
    SECRET_KEY: str = "SANPARRILLA_SUPER_SECRET_JWT_KEY_2026_FUEGO"

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            str(BASE_DIR / ".env"),
            str(BASE_DIR / "backend" / ".env")
        ),
        extra="ignore"
    )

settings = Settings()
