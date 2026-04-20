
"""
Application configuration management using Pydantic Settings.
Loads all environment variables and validates them at startup.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All secrets and configuration must come from .env file or environment.
    """
    
    # Database Configuration
    DATABASE_URL: str
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
