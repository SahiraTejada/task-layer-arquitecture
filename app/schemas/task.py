from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import PaginatedResponse
from app.schemas.tag import TagResponse
from app.utils.enum import PriorityEnum, TaskStatus

class TaskBase(BaseModel):
    name: str = Field(..., max_length=100, min_length=1, description="Task name (max 100 characters)")
    description: Optional[str] = Field(None, max_length=255, description="Description of the task (max 255 characters)")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")
    priority: Optional[PriorityEnum] = Field(default=PriorityEnum.MEDIUM, description="Priority level of the task")
    status: Optional[TaskStatus] = Field(default=TaskStatus.PENDING, description="Current status of the task")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Revisar informe",
                "description": "Analizar el informe trimestral",
                "due_date": "2025-07-01T12:00:00",
                "priority": "high",
                "status": "in_progress"
            }
        }

class TaskCreate(TaskBase):
    tag_ids: Optional[List[int]] = Field(default=[], description="List of tag IDs to associate with the task")


class TaskUpdate(TaskBase):
    id: int = Field(..., description="Task ID")
    name: Optional[str] = Field(None, max_length=100, min_length=1, description="Task name (max 100 characters)")
    description: Optional[str] = Field(None, max_length=255, description="Description of the task (max 255 characters)")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")
    priority: Optional[PriorityEnum] = Field(default=PriorityEnum.MEDIUM, description="Priority level of the task")
    status: Optional[TaskStatus] = Field(default=TaskStatus.PENDING, description="Current status of the task")

class TaskRequest(BaseModel):
    id: int = Field(..., description="Task ID")

class TaskResponse(TaskBase):
    id: int = Field(..., description="Task ID")
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True
    
class TaskListResponse(PaginatedResponse[TaskResponse]):
    pass

