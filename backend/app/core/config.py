from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CRM360"
    DATABASE_URL: str
    SECRET_KEY: str
    FRONTEND_URL: str = "http://localhost:5173"
    GOOGLE_CLIENT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
