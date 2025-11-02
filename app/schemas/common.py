from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Скільки записів повернути"
    )
    offset: int = Field(
        0,
        ge=0,
        description="Зсув від початку вибірки"
    )
    search: Optional[str] = Field(
        None,
        description="Опційний пошук"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    limit: int
    offset: int
    items: List[T]
