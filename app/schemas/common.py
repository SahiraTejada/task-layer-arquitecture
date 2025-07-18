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
    
    
class ErrorResponseSchema(BaseModel):
    """
    Standard schema for error HTTP responses.
    """
    error: str = Field(..., example="Unauthorized", description="Short summary of the error.")
    code: Optional[int] = Field(None, example=401, description="HTTP status code.")
    error_type: Optional[str] = Field(None, example="AuthenticationError", description="Specific error category.")
    detail: Optional[str] = Field(None, example="The access token is invalid or has expired.", description="Detailed explanation of the error.")
    field: Optional[str] = Field(None, example="email", description="Specific field related to the error, if applicable.")    