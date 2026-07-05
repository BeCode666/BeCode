"""Application configuration loaded from .env file."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    # LLM Configuration
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = "sk-your-api-key-here"
    openai_model: str = "gpt-4o"

    # Agent Workflow
    max_iterations: int = 10
    session_dir: str = "./sessions"

    # Log Level (only WARNING and above shown on console)
    log_level: str = "WARNING"

    model_config = {
        "env_file": str(env_path),
        "extra": "ignore",
    }


settings = Settings()
