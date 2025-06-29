from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import PaginatedResponse
from app.utils.enum import TagColorEnum

class TagBase(BaseModel):
    name: str = Field(..., description="Tag name")
    color: TagColorEnum = Field(..., description="Color of the tag")

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    id: int = Field(..., description="Tag ID")
    name: Optional[str] = Field(None, description="Updated name")
    color: Optional[TagColorEnum] = Field(None, description="Updated color")

class TagRequest(BaseModel):
    id: int = Field(..., description="Tag ID")

class TagResponse(TagBase):
    id: int = Field(..., description="Tag ID")
    
class TagListResponse(PaginatedResponse[TagResponse]):
    pass

