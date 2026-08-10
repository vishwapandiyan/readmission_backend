"""
Configuration settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Hospital Readmission Prediction API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database (SQLite - no installation required)
    DATABASE_URL: str = "sqlite:///./readmission.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # ML Model
    MODEL_PATH: str = "../best_model.pkl"
    FEATURE_IMPORTANCE_PATH: str = "../best_model_feature_importance.csv"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
