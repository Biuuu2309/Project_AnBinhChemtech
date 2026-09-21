from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "An Binh Chemtech Quote API"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./data/app.db"
    worker_poll_interval: int = 3
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
