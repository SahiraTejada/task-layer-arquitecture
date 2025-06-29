from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings

# Create SQLite engine
engine = create_engine(
    settings.DATABASE_URL,                    # Database URL (e.g. sqlite:///./test.db)
    connect_args={"check_same_thread": False} # SQLite-specific argument to allow use with multiple threads
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,   # Disable autocommit; changes must be explicitly committed
    autoflush=False,    # Disable autoflush to control when changes are sent to the DB
    bind=engine         # Bind this session to the engine we created
)

# Base class for declarative class definitions (your models will inherit from this)
Base = declarative_base()


# Dependency function to provide a database session to path operations (for example, in FastAPI)
def get_db():
    db = SessionLocal()  # Create a new SessionLocal instance (database session)
    try:
        yield db        # Yield the session, allowing usage in a 'with' or dependency injection
    finally:
        db.close()      #Ensure the session is closed after use, preventing connections from leaking
