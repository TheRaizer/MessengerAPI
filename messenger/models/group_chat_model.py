from pydantic import BaseModel


class CreateGroupChatModel(BaseModel):
    group_chat_name: str
    usernames: list[str]


class GroupChatModel(BaseModel):
    group_chat_id: int
    name: str

    class Config:
        orm_mode = True
