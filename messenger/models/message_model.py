from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateMessageModel(BaseModel):
    content: str
    group_chat_id: Optional[int]


class BaseMessageModel(CreateMessageModel):
    created_date_time: datetime
    last_edited_date_time: Optional[datetime]
    seen: bool


class MessageModel(BaseMessageModel):
    message_id: int
    sender_id: int
    reciever_id: int

    class Config:
        orm_mode = True
