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
    
    # Database components
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "readmission_db"
    DB_USER: str = "vishwa"
    DB_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """Construct database URL from components"""
        driver = "postgresql+asyncpg" if async_driver else "postgresql"
        if self.DB_PASSWORD:
            return f"{driver}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"{driver}://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:5173",
        "https://d578gwwut8r88.cloudfront.net",
        "http://3.238.62.41:8000"  # Allow API to call itself
    ]
    
    # ML Model
    MODEL_PATH: str = "../best_model.pkl"
    FEATURE_IMPORTANCE_PATH: str = "../best_model_feature_importance.csv"
    
    # LLM Settings (Groq API)
    GROQ_API_KEY: str = "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"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    LLM_ENABLED: bool = True
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048


settings = Settings()

# Construct database URLs after settings instantiation
DATABASE_URL = settings.get_database_url(async_driver=True)
DATABASE_URL_SYNC = settings.get_database_url(async_driver=False)
