from pydantic import BaseModel, Field
from typing import Any, Generic, Optional, TypeVar, List

T = TypeVar("T")
class PaginationBase(BaseModel):
    page: int = Field(1, ge=1, description="Page number (must be >= 1)")
    limit: int = Field(10, ge=1, le=100, description="Number of items per page (between 1 and 100)")

class PaginationRequest(PaginationBase):
    pass


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""
    items: List[T]
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Limit per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")



class SuccessResponseSchema(BaseModel):
    """
    Standard schema for successful HTTP responses.
    """
    message: str = Field(..., example="Operation completed successfully.")
    data: Optional[Any] = Field(
        None,
        description="Optional data returned by the operation."
    )
    
