# Import required SQLAlchemy classes
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

# Import your custom base model that inherits from declarative_base()
from .base import BaseModel


# Define the User model, which maps to the "users" table in the database
class User(BaseModel):
    __tablename__ = "users"  # Explicitly sets the table name to "users"

    # --------------------
    # Fields / Columns
    # --------------------

    email = Column(String, unique=True, index=True, nullable=False)
    # Email field:
    # - String type
    # - Must be unique
    # - Indexed for faster search
    # - Cannot be null

    username = Column(String(50), unique=True, index=True, nullable=False)
    # Username field:
    # - String with a max length of 50 characters
    # - Must be unique
    # - Indexed
    # - Cannot be null

    hashed_password = Column(String, nullable=False)
    # Field to store the hashed (encrypted) password
    # - String type
    # - Required field (cannot be null)

    is_active = Column(Boolean, default=True)
    # Boolean field to indicate whether the user is active
    # - Defaults to True

    # --------------------
    # Relationships
    # --------------------

    tasks = relationship(
        "Task",                      # Reference to the Task model (as a string)
        back_populates="user",       # Refers to the attribute in Task that points back to User
        cascade="all, delete-orphan" # Automatically deletes all related tasks if the user is deleted
    )

    tags = relationship(
        "Tag",                       # Reference to the Tag model
        back_populates="user",       # Refers to the attribute in Tag that points back to User
        cascade="all, delete-orphan" # Automatically deletes all related tags if the user is deleted
    )
