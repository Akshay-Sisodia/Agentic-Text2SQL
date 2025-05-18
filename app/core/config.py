"""Configuration settings for the Text-to-SQL system."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        case_sensitive=False
    )

    # Project information
    PROJECT_NAME: str = "Agentic Text-to-SQL"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Production-Level Agentic Text-to-SQL System with PydanticAI"

    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default=False)

    # Database settings
    DATABASE_URL: Optional[str] = None
    DB_TYPE: str = Field(default="sqlite")  # postgresql, mysql, sqlite, etc.
    DB_NAME: str = Field(default="text2sql")
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    
    # Conversation database settings
    CONVERSATION_DB_URL: Optional[str] = None

    # LLM settings
    LLM_PROVIDER: str = Field(default="groq")  # groq, openai, anthropic, etc.
    LLM_MODEL: str = Field(default="llama-3.3-70b-versatile", env="LLM_MODEL")
    LLM_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = Field(default=0.1)
    LLM_MAX_TOKENS: int = Field(default=1024)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")


# Create global settings object
settings = Settings()

# Set GROQ_API_KEY env variable for Groq provider if not already set
if settings.LLM_API_KEY and not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = settings.LLM_API_KEY
