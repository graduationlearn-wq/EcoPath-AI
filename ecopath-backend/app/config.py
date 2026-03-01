"""
Configuration settings for EcoPath AI backend.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "EcoPath AI"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Base weights for eco-cost calculation
    WEIGHT_TRAFFIC_BASE: float = float(os.getenv("WEIGHT_TRAFFIC_BASE", "0.3"))
    WEIGHT_AQI_BASE: float = float(os.getenv("WEIGHT_AQI_BASE", "0.4"))
    WEIGHT_GRADIENT_BASE: float = float(os.getenv("WEIGHT_GRADIENT_BASE", "0.2"))
    WEIGHT_CARPOOL_BASE: float = float(os.getenv("WEIGHT_CARPOOL_BASE", "0.1"))
    WEIGHT_GREENERY_BASE: float = float(os.getenv("WEIGHT_GREENERY_BASE", "0.15"))

    # External API Keys
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()