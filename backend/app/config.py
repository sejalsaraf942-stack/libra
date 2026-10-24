from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(_BACKEND_DIR / ".env"), str(_REPO_ROOT / ".env"), ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite:///./libra.db"
    otp_provider: str = "mock"
    sms_api_key: str = ""
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_model: str = ""
    vector_store: str = "faiss"
    faiss_index_path: str = "./data/faiss"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    normal_daily_limit: int = 10
    professional_daily_limit: int = 100
    quota_reset_tz: str = "Asia/Kolkata"
    payment_provider: str = "mock"


settings = Settings()
