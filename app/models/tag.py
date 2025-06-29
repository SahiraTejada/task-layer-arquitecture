from sqlalchemy import Column, Integer, String, Table, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.utils.enum import TagColorEnum
from .base import BaseModel

# Association table for many-to-many relationship between tasks and tags
task_tag_association = Table(
    "task_tag_association",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)


class Tag(BaseModel):
    __tablename__ = "tags"
    
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(SQLEnum(TagColorEnum,native_enum=False), nullable=False, default=TagColorEnum.BLUE)
    
    # Many-to-many relationship with tasks
    tasks = relationship("Task", secondary=task_tag_association, back_populates="tags")