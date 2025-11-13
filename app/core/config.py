"""
Application configuration and settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Product Importer"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: Optional[str] = None
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Redis
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # File Upload
    max_file_size_mb: int = 100
    upload_directory: str = "uploads"
    chunk_size: int = 1000  # Records per batch
    
    # API
    api_v1_str: str = "/api/v1"
    cors_origins: list = ["*"]
    
    # Production settings
    secret_key: str = "your-secret-key-change-in-production"
    
    # Optional environment field (for backward compatibility)
    environment: Optional[str] = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in environment
    
    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL."""
        if self.database_url:
            # Ensure we use the async driver for SQLAlchemy
            url = self.database_url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return "postgresql+asyncpg://postgres:password@localhost:5432/product_importer"
    
    @property
    def effective_redis_url(self) -> str:
        """Get the effective Redis URL."""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def effective_celery_broker_url(self) -> str:
        """Get the effective Celery broker URL."""
        return self.celery_broker_url or self.effective_redis_url
    
    @property
    def effective_celery_result_backend(self) -> str:
        """Get the effective Celery result backend URL."""
        return self.celery_result_backend or self.effective_redis_url


settings = Settings()