"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "RacingLineAI"

    # CORS — wildcard subdomains handled by allow_origin_regex in main.py
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://racinglin-ai.vercel.app",
    ]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/racingline"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour

    # FastF1 Settings
    FASTF1_CACHE_DIR: str = ".fastf1_cache"

    # ML Model Settings
    MODELS_DIR: str = "app/ml_models/weights"
    LSTM_MODEL_PATH: str = "app/ml_models/weights/lstm_model.pkl"
    REGRESSION_MODEL_PATH: str = "app/ml_models/weights/regression_model.pkl"
    STRATEGY_MODEL_PATH: str = "app/ml_models/weights/strategy_model.pkl"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
