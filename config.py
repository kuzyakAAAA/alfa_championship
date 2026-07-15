"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the application."""

    app_name: str = os.getenv("APP_NAME", "Альфа Бизнес AI")
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'alfa_business.db'}"
    )
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "mock-finance-assistant")


settings = Settings()
APP_NAME = settings.app_name
DATA_DIR = settings.data_dir
DATABASE_URL = settings.database_url
LLM_API_KEY = settings.llm_api_key
LLM_MODEL = settings.llm_model
