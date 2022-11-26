from typing import Optional
from pydantic import BaseModel


class ValidityData(BaseModel):
    is_valid: bool
    detail: Optional[str]