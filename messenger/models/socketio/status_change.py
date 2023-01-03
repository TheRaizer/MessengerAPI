from pydantic import BaseModel


class StatusChangeEventData(BaseModel):
    user_id: int
    status: str


class FriendStatusChangeEventData(StatusChangeEventData):
    friend_id: int
