"""
Configuration management for the Outreach Engine
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using environment variables and .env file"""

    # Application
    APP_NAME: str = "Cold Outreach Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1

    # Model Configuration
    MODEL_NAME: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    DEVICE: str = "cpu"
    MAX_TOKENS: int = 512
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"
    CACHE_DIR: Optional[Path] = None

    # Database
    DB_PATH: Path = DATA_DIR / "profiles.db"
    STORAGE_PATH: Path = DATA_DIR / "storage"

    # API Configuration
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    # Feature Flags
    USE_CACHE: bool = True
    ENABLE_ANALYTICS: bool = True
    STORE_PROFILES: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **data):
        super().__init__(**data)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.STORAGE_PATH.mkdir(parents=True, exist_ok=True)

        if self.CACHE_DIR is None:
            self.CACHE_DIR = self.MODELS_DIR / ".cache"
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
