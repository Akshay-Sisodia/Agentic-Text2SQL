"""
Configuration settings for the application.
"""

import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_PREFIX: str = "/api"

    # Project info
    PROJECT_NAME: str = "Agentic Text2SQL"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A Text-to-SQL interface with agentic capabilities"

    # CORS settings
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,https://text2sql.akshaysisodia.studio",
    ).split(",")

    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # SQLite default path
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "sample_huge.db")

    # Conversation database settings
    CONVERSATION_DB_URL: Optional[str] = os.getenv(
        "CONVERSATION_DB_URL", "sqlite:///conversations.db"
    )

    # Model settings
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "claude-3-sonnet-20240229")

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False
    
    def validate_model_api_keys(self, model_name: str) -> bool:
        """
        Validate that the necessary API keys are present for the specified model.
        
        Args:
            model_name: The name of the model to validate
            
        Returns:
            bool: True if the required API key is present, False otherwise
        """
        if not model_name:
            return False
            
        model_name_lower = model_name.lower()
        
        if any(name in model_name_lower for name in ["claude", "anthropic"]):
            return self.ANTHROPIC_API_KEY is not None and len(self.ANTHROPIC_API_KEY.strip()) > 0
        elif any(name in model_name_lower for name in ["gpt", "openai", "davinci", "turbo"]):
            return self.OPENAI_API_KEY is not None and len(self.OPENAI_API_KEY.strip()) > 0
        elif any(name in model_name_lower for name in ["llama", "mistral", "gemini"]):
            # Add validation for other providers as needed
            # This is a placeholder for future expansion
            return False
            
        # For unknown models, assume validation fails
        return False
        
    def get_model_provider(self, model_name: str) -> Optional[str]:
        """
        Determine the provider for a given model name.
        
        Args:
            model_name: The name of the model
            
        Returns:
            Optional[str]: The provider name or None if unknown
        """
        if not model_name:
            return None
            
        model_name_lower = model_name.lower()
        
        if any(name in model_name_lower for name in ["claude", "anthropic"]):
            return "anthropic"
        elif any(name in model_name_lower for name in ["gpt", "openai", "davinci", "turbo"]):
            return "openai"
        elif "llama" in model_name_lower:
            return "llama"
        elif "mistral" in model_name_lower:
            return "mistral"
        elif "gemini" in model_name_lower:
            return "google"
            
        return None


# Create settings instance
settings = Settings()
