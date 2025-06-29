# Import SQLAlchemy components to define columns and use database functions
from sqlalchemy import Column, Integer, DateTime, func

# Import the Base class from your config (usually created using declarative_base())
from app.config.database import Base


# BaseModel is an abstract class that provides common fields for all models
class BaseModel(Base):
    __abstract__ = True
    # This tells SQLAlchemy not to create a table for this model.
    # Instead, other models can inherit from it to get these columns.

    id = Column(Integer, primary_key=True, index=True)
    # Unique identifier for each record.
    # - Integer type
    # - Primary key of the table
    # - Automatically incremented
    # - Indexed for faster querying

    created_at = Column(
        DateTime(timezone=True),        # Stores timestamp with timezone
        nullable=False,                 # Cannot be null
        server_default=func.now()       # Automatically set to current time on insert (handled by DB)
    )
    # Timestamp indicating when the record was created.

    updated_at = Column(
        DateTime(timezone=True),        # Timestamp with timezone
        nullable=True,                  # Can be null initially
        server_default=func.now(),      # Default value at insert
        onupdate=func.now()             # Automatically updates timestamp when record is modified
    )
    # Timestamp for the last time the record was updated.

    deleted_at = Column(
        DateTime(timezone=True),        # Timestamp with timezone
        nullable=True                   # Can be null if not deleted
    )
    # Used for soft deletion:
    # Instead of deleting a record from the DB, set this field to mark it as deleted.
