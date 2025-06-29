# Import necessary SQLAlchemy components for defining tables, columns, relationships, and enums
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

# Import the Base class for declarative models (usually from declarative_base)
from app.config.database import Base
# Import custom Enum for tag colors
from app.utils.enum import TagColorEnum
# Import BaseModel with common fields (id, timestamps, etc.)
from .base import BaseModel


# Association table to establish many-to-many relationship between tasks and tags
task_tag_association = Table(
    "task_tag_association",      # Name of the association table in the DB
    Base.metadata,               # Metadata object to register the table

    # Foreign key column linking to 'tasks' table's 'id' column
    Column(
        "task_id",              # Column name in association table
        Integer,                # Integer type
        ForeignKey("tasks.id", ondelete="CASCADE"),  # Delete association if task is deleted
        primary_key=True        # Part of the composite primary key
    ),

    # Foreign key column linking to 'tags' table's 'id' column
    Column(
        "tag_id",               # Column name in association table
        Integer,                # Integer type
        ForeignKey("tags.id", ondelete="CASCADE"),   # Delete association if tag is deleted
        primary_key=True        # Part of the composite primary key
    )
)


# Define the Tag model representing the 'tags' table
class Tag(BaseModel):
    __tablename__ = "tags"  # Explicit table name

    # --------------------
    # Columns / Fields
    # --------------------

    name = Column(
        String(50),            # String column with max length 50
        unique=True,           # Tag names must be unique
        index=True,            # Indexed for faster lookups
        nullable=False         # Required field
    )

    color = Column(
        SQLEnum(TagColorEnum, native_enum=False),  # Enum stored as string for tag color
        nullable=False,                            # Required field
        default=TagColorEnum.BLUE                   # Default color value
    )

    user_id = Column(
        Integer,                 # Integer type column
        ForeignKey("users.id", ondelete="CASCADE"),  # Foreign key to the 'users' table
        nullable=False           # Required field - tag must belong to a user
    )

    # --------------------
    # Relationships
    # --------------------

    user = relationship(
        "User",                  # Related model is User
        back_populates="tags"    # Corresponds to 'tags' attribute on User model
    )

    tasks = relationship(
        "Task",                          # Related model is Task
        secondary=task_tag_association,  # Uses the many-to-many association table
        back_populates="tags"            # Corresponds to 'tags' attribute on Task model
    )
