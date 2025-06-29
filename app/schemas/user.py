from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.task import TaskResponse

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User Email")
    username: str = Field(..., max_length=50, min_length=3)
    password: str = Field(..., min_length=8, description="Password in plain text, min 8 chars")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    id:int = Field(..., description="User ID")
    username: Optional[str] = Field(None, max_length=50, min_length=3)
    password: Optional[str] = Field(None, min_length=8, description="Password in plain text, min 8 chars")

class UserResponse(BaseModel):
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User Email")
    username: str = Field(..., max_length=50, min_length=3)
    is_active: bool = Field(..., description="Is user active")
    tasks: List[TaskResponse] = []

    class Config:
        orm_mode = True

