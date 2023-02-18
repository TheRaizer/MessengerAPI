from typing import Optional
from pydantic import BaseModel


class SocketioAccessTokenData(BaseModel):
    user_id: Optional[int] = None
    type: str = "socket"
