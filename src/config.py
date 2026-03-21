import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = "your_api_key_here" # Заглушка
    
    # Читаем из .env, игнорируя лишнее
    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env", extra='ignore')

settings = Settings()