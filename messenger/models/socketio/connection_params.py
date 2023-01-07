from pydantic import BaseModel


class OnConnectionParams(BaseModel):
    sid: str
    current_user_id: int


class OnDisconnectionParams(BaseModel):
    sid: str
