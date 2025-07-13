from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.common import PaginatedResponse
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
    user_id:int = Field(..., description="User ID")
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
        from_attributes = True
        
        
class UserWithTasksResponse(UserResponse):
    tasks: List[TaskResponse] = Field(default=[], description="User tasks")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    
    
class UserChangePassword(BaseModel):
    user_id: int = Field(..., description="User ID")
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v    

class UserFilters(BaseModel):
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    username: Optional[str] = Field(None, description="Filter by username")
    email: Optional[str] = Field(None, description="Filter by email")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date after")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date before")

class UserBulkUpdate(BaseModel):
    """Schema for bulk user updates."""
    user_ids: List[int] = Field(..., min_items=1, description="List of user IDs to update")
    update_data: UserUpdate = Field(..., description="Data to update for all users")


class UserPaginatedResponse(PaginatedResponse[UserResponse]):
    """Paginated response schema for users."""
    pass   

class UserSearch(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of records to return")
