from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import PaginatedResponse

class TaskBase(BaseModel):
    name: str = Field(..., description="Task name")
    color: TaskColorEnum = Field(..., description="Color of the Task")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    id: int = Field(..., description="Task ID")
    name: Optional[str] = Field(None, description="Updated name")
    color: Optional[TaskColorEnum] = Field(None, description="Updated color")

class TaskRequest(BaseModel):
    id: int = Field(..., description="Task ID")

class TaskResponse(TaskBase):
    id: int = Field(..., description="Task ID")
    
class TaskListResponse(PaginatedResponse[TaskResponse]):
    pass

