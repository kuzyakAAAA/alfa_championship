"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


ALLOWED_GIGACHAT_SCOPES = {"GIGACHAT_API_PERS", "GIGACHAT_API_B2B", "GIGACHAT_API_CORP"}


def _optional_env(name: str) -> str | None:
    """Return a stripped optional environment value."""

    value = os.getenv(name, "").strip()
    return value or None


def _integer_env(name: str, default: int, minimum: int = 1) -> int:
    """Read a bounded integer without making malformed .env values fatal."""

    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    """Read a bounded float without making malformed .env values fatal."""

    try:
        return min(maximum, max(minimum, float(os.getenv(name, str(default)))))
    except (TypeError, ValueError):
        return default


def _boolean_env(name: str, default: bool) -> bool:
    """Parse common boolean environment spellings with a safe fallback."""

    value = os.getenv(name, str(default)).strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    return default


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the application."""

    app_name: str = os.getenv("APP_NAME", "Альфа Бизнес AI")
    data_dir: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'alfa_business.db'}"
    )
    gigachat_credentials: str | None = _optional_env("GIGACHAT_CREDENTIALS")
    gigachat_scope: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()
    gigachat_model: str = os.getenv("GIGACHAT_MODEL", "GigaChat-2").strip() or "GigaChat-2"
    gigachat_max_tokens: int = _integer_env("GIGACHAT_MAX_TOKENS", 700)
    gigachat_temperature: float = _float_env("GIGACHAT_TEMPERATURE", 0.1, 0.0, 2.0)
    gigachat_timeout: float = _float_env("GIGACHAT_TIMEOUT", 30.0, 1.0, 300.0)
    gigachat_verify_ssl_certs: bool = _boolean_env("GIGACHAT_VERIFY_SSL_CERTS", True)
    gigachat_ca_bundle_file: str | None = _optional_env("GIGACHAT_CA_BUNDLE_FILE")

    def __post_init__(self) -> None:
        """Replace an unsupported scope with the personal API default."""

        if self.gigachat_scope not in ALLOWED_GIGACHAT_SCOPES:
            object.__setattr__(self, "gigachat_scope", "GIGACHAT_API_PERS")


settings = Settings()
APP_NAME = settings.app_name
DATA_DIR = settings.data_dir
DATABASE_URL = settings.database_url
GIGACHAT_CREDENTIALS = settings.gigachat_credentials
GIGACHAT_SCOPE = settings.gigachat_scope
GIGACHAT_MODEL = settings.gigachat_model
GIGACHAT_MAX_TOKENS = settings.gigachat_max_tokens
GIGACHAT_TEMPERATURE = settings.gigachat_temperature
GIGACHAT_TIMEOUT = settings.gigachat_timeout
GIGACHAT_VERIFY_SSL_CERTS = settings.gigachat_verify_ssl_certs
GIGACHAT_CA_BUNDLE_FILE = settings.gigachat_ca_bundle_file
