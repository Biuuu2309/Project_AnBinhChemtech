from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "An Binh Chemtech Quote API"
    secret_key: str = "change-me"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'app.db').as_posix()}"
    worker_poll_interval: int = 3
    cors_origins: str = "http://localhost:5173"
    # Download/complete may only reference files under this dir (default: worker/output)
    quotation_output_dir: str = str((PROJECT_ROOT / "worker" / "output").as_posix())


settings = Settings()
