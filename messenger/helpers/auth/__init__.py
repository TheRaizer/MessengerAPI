"""Declare validity pydantic model that will be used in validation of 
username, email and password.
"""

from typing import Optional
from pydantic import BaseModel


class ValidityData(BaseModel):
    is_valid: bool
    detail: Optional[str]
