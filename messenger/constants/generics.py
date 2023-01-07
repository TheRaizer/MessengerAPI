from typing import TypeVar
from pydantic import BaseModel

from sqlalchemy import Table


T = TypeVar("T", bound=Table)
B = TypeVar("B", bound=BaseModel)
S = TypeVar("S")
