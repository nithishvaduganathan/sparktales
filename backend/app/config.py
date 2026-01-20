"""Application configuration settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
import secrets


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "SparkTales LMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sparktales.db"
    
    # JWT - No default value to force configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Super Admin
    SUPER_ADMIN_EMAIL: str = "superadmin@sparktales.com"
    SUPER_ADMIN_PASSWORD: str = "SuperAdmin123!"
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".txt", ".docx"]
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RAG_CONTEXT_MAX_LENGTH: int = 1500
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
