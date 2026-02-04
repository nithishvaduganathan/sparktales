"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # AWS General
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # AWS Cognito
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_client_secret: Optional[str] = None
    cognito_domain: str
    
    # AWS S3
    s3_bucket_name: str
    s3_region: str = "us-east-1"
    
    # Database (RDS)
    database_url: str
    
    # Application
    app_secret_key: str = "change-this-secret-key"
    frontend_url: str = "http://localhost:5173"
    
    # OpenAI (optional)
    openai_api_key: Optional[str] = None
    
    # Google Gemini (for RAG)
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cache settings for performance"""
    return Settings()
