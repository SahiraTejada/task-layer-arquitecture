from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import PaginatedResponse
from app.utils.enum import TagColorEnum

class TagBase(BaseModel):
    name: str = Field(..., max_length=50, min_length=1,  description="Tag name (max 50 characters)")
    color: TagColorEnum = Field(..., description="Color of the tag")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Urgent",
                "color": "red"
            }
        }
        
class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    id: int = Field(..., description="Tag ID")
    name: Optional[str] = Field(None,max_length=50, min_length=1, description="Updated name")
    color: Optional[TagColorEnum] = Field(None, description="Updated color")

class TagRequest(BaseModel):
    id: int = Field(..., description="Tag ID")

class TagResponse(TagBase):
    id: int = Field(..., description="Tag ID")
    class Config:
        from_attributes = True
    
class TagListResponse(PaginatedResponse[TagResponse]):
    pass

