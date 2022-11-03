from datetime import datetime
from typing import Union
from pydantic import BaseModel

class CreateMessageModel(BaseModel):
    content: str
    group_chat_id: Union[int, None]
    

class MessageModel(CreateMessageModel):
    message_id: int
    sender_id: int
    reciever_id: int
    created_date_time: datetime
    last_edited_date_time: datetime
    seen: bool
    
    class Config:
        orm_mode = True
        