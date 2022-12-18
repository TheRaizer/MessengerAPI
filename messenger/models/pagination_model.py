from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel


class CursorModel(BaseModel):
    prev_page: Optional[str]
    next_page: Optional[str]


T = TypeVar("T")


class CursorPaginationModel(BaseModel, Generic[T]):
    cursor: CursorModel
    results: List[T]
