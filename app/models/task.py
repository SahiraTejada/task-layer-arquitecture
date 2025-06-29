from sqlalchemy import Column, DateTime, ForeignKey, Integer, String,Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.utils.enum import PriorityEnum, TaskStatus
from .base import BaseModel
from .tag import task_tag_association
    
class Task(BaseModel):
    __tablename__ = "tasks"
    
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(SQLEnum(PriorityEnum,native_enum=False), nullable=True, default=PriorityEnum.MEDIUM)
    status = Column(SQLEnum(TaskStatus,native_enum=False), nullable=False, default=TaskStatus.PENDING)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="tasks")

    tags = relationship("Tag", secondary=task_tag_association, back_populates="tasks")