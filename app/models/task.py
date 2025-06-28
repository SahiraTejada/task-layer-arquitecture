from enum import Enum
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.utils.enum import PriorityEnum
from .base import BaseModel
from .tag import task_tag_association
    
class Task(BaseModel):
    __tablename__ = "tasks"
    
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    due_date = Column(String, nullable=False)
    priority = Column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM)
    tag_id = Column(Integer, ForeignKey("tag.id"))
    is_completed = Column(Boolean, default=False)

    # Relationship with tasks
    tags = relationship("Tag", secondary=task_tag_association, back_populates="tasks")
