from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./task_manager.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    PROJECT_NAME: str = "Task Manager API"
    PROJECT_DESCRIPTION: str = "API for task management with priorities, tags, and time"
    DEBUG: bool = True
    VERSION:str = "1.0.0"
    class Config:
        env_file = ".env"

settings = Settings()