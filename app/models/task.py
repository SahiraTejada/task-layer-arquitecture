from sqlalchemy import Column, ForeignKey, Integer, String,Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.utils.enum import PriorityEnum, TaskStatus
from .base import BaseModel
from .tag import task_tag_association
    
class Task(BaseModel):
    __tablename__ = "tasks"
    
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    due_date = Column(String, nullable=False)
    priority = Column(SQLEnum(PriorityEnum,native_enum=False), nullable=False, default=PriorityEnum.MEDIUM)
    tag_id = Column(Integer, ForeignKey("tags.id"))
    status = Column(SQLEnum(TaskStatus,native_enum=False), default=TaskStatus.PENDING)

    # Relationship with tasks
    tags = relationship("Tag", secondary=task_tag_association, back_populates="tasks")
