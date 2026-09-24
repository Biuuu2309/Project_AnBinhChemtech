from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

WORKER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WORKER_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_url: str = "http://127.0.0.1:8000"
    worker_poll_interval: int = 3
    use_codex_cli: bool = False
    ai_note_enabled: bool = True
    ai_fail_job_on_error: bool = False
    template_path: str = str(WORKER_DIR / "templates" / "quotation_template.docx")
    output_dir: str = str(WORKER_DIR / "output")


settings = Settings()
