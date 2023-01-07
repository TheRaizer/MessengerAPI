from typing import Optional
from pydantic import BaseModel


class AccessTokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
