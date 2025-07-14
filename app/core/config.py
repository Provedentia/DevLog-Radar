from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://devlog:devlog@localhost:5432/devlog"
    REDIS_URL: str = "redis://localhost:6379/0"
    GITHUB_TOKEN: Optional[str] = None
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()