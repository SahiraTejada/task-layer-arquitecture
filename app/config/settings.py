# Import BaseSettings from pydantic_settings to define config with environment variable support
from pydantic_settings import BaseSettings

# Define a class that holds all your app settings
class Settings(BaseSettings):
    # ---------------------
    # Database Configuration
    # ---------------------
    
    DATABASE_URL: str = "sqlite:///./task_manager.db"
    # This is the default SQLite database URL.
    # You can override it via environment variables (like in a .env file).

    # ---------------------
    # Security Configuration
    # ---------------------
    
    SECRET_KEY: str = "your-secret-key-here"
    # Used for signing JWT tokens or other secure values. Should be kept secret in production.

    ALGORITHM: str = "HS256"
    # The algorithm used for encoding JWT tokens. HS256 is a common HMAC + SHA-256 method.

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Token expiration time in minutes for authentication sessions.

    # ---------------------
    # Application Info
    # ---------------------
    
    PROJECT_NAME: str = "Task Manager API"
    # Name of your FastAPI project.

    PROJECT_DESCRIPTION: str = "API for task management with priorities, tags, and time"
    # A short description of what your API does (used in docs like Swagger UI).

    DEBUG: bool = True
    # Toggle for enabling debug mode (should be False in production).

    VERSION: str = "1.0.0"
    # Application version number.

    # ---------------------
    # Pydantic Settings Config
    # ---------------------
    class Config:
        env_file = ".env"
        # This tells Pydantic to load environment variables from a `.env` file if present.

# Instantiate the settings object so it can be imported and used throughout the app
settings = Settings()
