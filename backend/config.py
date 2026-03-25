from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENROUTER_API_KEY: str
    OPENAI_API_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_API_MODEL: str = "google/gemini-3-flash-preview"
    
    RAILWAY_REMOTE_SSE_URL: str
    AMAP_REMOTE_SSE_URL: str
    TAVILY_REMOTE_SSE_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings()
