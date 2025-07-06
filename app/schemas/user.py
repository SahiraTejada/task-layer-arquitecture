from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.task import TaskResponse

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User Email")
    username: str = Field(..., max_length=50, min_length=3)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password in plain text, min 8 chars")
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @field_validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v.lower()
    



class UserUpdate(BaseModel):
    id:int = Field(..., description="User ID")
    username: Optional[str] = Field(None, max_length=50, min_length=3)
    password: Optional[str] = Field(None, min_length=8, description="Password in plain text, min 8 chars")
    
    @field_validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @field_validator('username')
    def validate_username(cls, v):
        if v is not None and not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v.lower() if v else v

class UserResponse(BaseModel):
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User Email")
    username: str = Field(..., max_length=50, min_length=3)
    is_active: bool = Field(..., description="Is user active")

    class Config:
        orm_mode = True
        
        
class UserWithTaskResponse(UserResponse):
    tasks: List[TaskResponse] = Field(default=[], description="User tasks")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    
    
class UserChangePassword(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v    