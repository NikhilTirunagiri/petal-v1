"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_role: str = Field(..., alias="SUPABASE_SERVICE_ROLE")

    # Anthropic (Claude)
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")

    # OpenAI (Embeddings)
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # Mem0
    mem0_api_key: str = Field(..., alias="MEM0_API_KEY")

    # App Config
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
