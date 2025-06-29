from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List
from pydantic.generics import GenericModel

T = TypeVar("T")
class PaginationBase(BaseModel):
    page: int = Field(1, ge=1, description="Page number (must be >= 1)")
    limit: int = Field(10, ge=1, le=100, description="Number of items per page (between 1 and 100)")

class PaginationRequest(PaginationBase):
    pass


class PaginatedResponse(GenericModel, Generic[T]):
    items: List[T]
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Limit per page")
    total: int = Field(..., description="Total number of items")

