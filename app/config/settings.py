from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./task_manager.db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App
    app_name: str = "Task Manager API"
    debug: bool = True
    version:str = "1.0.0"
    class Config:
        env_file = ".env"

settings = Settings()