from typing import Generic, List, Optional
from pydantic import BaseModel
from pydantic.generics import GenericModel
from messenger.constants.generics import S


class CursorModel(BaseModel):
    prev_page: Optional[str]
    next_page: Optional[str]


class CursorPaginationModel(GenericModel, Generic[S]):
    cursor: CursorModel
    results: List[S]
