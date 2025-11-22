"""Configuration management for Respondr.ai backend."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "respondr_hospitals")
    
    # Watson Speech-to-Text
    watson_stt_apikey: Optional[str] = os.getenv("WATSON_STT_APIKEY")
    watson_stt_url: Optional[str] = os.getenv("WATSON_STT_URL")
    
    # watsonx.ai
    watsonx_api_key: Optional[str] = os.getenv("WATSONX_API_KEY")
    watsonx_project_id: Optional[str] = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    
    # Orchestrate Mode
    orchestrate_mode: str = os.getenv("ORCHESTRATE_MODE", "local")  # "local" or "production"
    orchestrate_instance_url: Optional[str] = os.getenv("ORCHESTRATE_INSTANCE_URL")
    orchestrate_agent_id: Optional[str] = os.getenv("ORCHESTRATE_AGENT_ID")
    orchestrate_api_key: Optional[str] = os.getenv("ORCHESTRATE_API_KEY")
    
    # Application
    app_name: str = "Respondr.ai API"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def validate_required_settings():
    """Validate that required settings are present."""
    errors = []
    
    if not settings.mongodb_uri:
        errors.append("MONGODB_URI is required")
    
    if errors:
        raise ValueError(f"Missing required configuration: {', '.join(errors)}")


# Validate on module import
try:
    validate_required_settings()
except ValueError as e:
    print(f"⚠️  Configuration Warning: {e}")
