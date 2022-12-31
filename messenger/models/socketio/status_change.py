from pydantic import BaseModel


class StatusChange(BaseModel):
    user_id: int
    status: str
