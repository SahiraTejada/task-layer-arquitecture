# Import required SQLAlchemy components
from typing import Optional
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

# Import custom enums for task priority and status
from app.utils.enum import PriorityEnum, TaskStatus

# Import custom base model with id, created_at, updated_at, etc.
from .base import BaseModel

# Import the many-to-many association table for tasks and tags
from .tag import task_tag_association


# Define the Task model representing the "tasks" table in the database
class Task(BaseModel):
    __tablename__ = "tasks"  # Explicit name for the table

    # --------------------
    # Columns / Fields
    # --------------------

    name = Column(String(100), index=True, nullable=False)
    # Task name:
    # - Up to 100 characters
    # - Indexed for faster searching
    # - Cannot be null

    description = Column(String(255), nullable=True)
    # Optional description of the task:
    # - Up to 255 characters
    # - Can be null

    due_date = Column(DateTime, nullable=True)
    # Optional due date for the task:
    # - DateTime type
    # - Can be null

    priority: Mapped[Optional[PriorityEnum]] = Column(
        SQLEnum(PriorityEnum, native_enum=False),  # Store enum as string
        nullable=True,
        default=PriorityEnum.MEDIUM                # Default value if none is provided
    )
    # Priority of the task:
    # - Uses custom enum PriorityEnum (LOW, MEDIUM, HIGH)
    # - Optional field with a default value

    status: Mapped[TaskStatus] = Column(
        SQLEnum(TaskStatus, native_enum=False),    # Store enum as string
        nullable=False,
        default=TaskStatus.PENDING                 # Default status
    )
    # Status of the task:
    # - Uses custom enum TaskStatus (PENDING, IN_PROGRESS, COMPLETED)
    # - Required field

    completed_at = Column(DateTime, nullable=True)
    # Timestamp for when the task is marked as completed:
    # - Optional field

    user_id = Column(Integer, ForeignKey("users.id"))
    # Foreign key linking the task to a user:
    # - Integer type
    # - References 'id' in the 'users' table

    user = relationship("User", back_populates="tasks")
    # Relationship to the User model:
    # - Allows access to the user object (task.user)
    # - Must match 'back_populates="tasks"' in the User model

    tags = relationship(
        "Tag",                           # Reference to the Tag model
        secondary=task_tag_association,  # Use the association table for many-to-many relation
        back_populates="tasks"           # Must match 'back_populates="tags"' in the Tag model
    )
    # Many-to-many relationship between Task and Tag:
    # - A task can have many tags, and a tag can be associated with many tasks
