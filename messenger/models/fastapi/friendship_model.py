from datetime import datetime
from pydantic import BaseModel


class FriendshipModel(BaseModel):
    requester_id: int
    addressee_id: int
    created_date_time: datetime

    class Config:
        orm_mode = True
