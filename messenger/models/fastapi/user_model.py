from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PrivateUserModel(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[datetime] = None

    class Config:
        orm_mode = True


class PublicUserModel(BaseModel):
    user_id: int
    username: str

    class Config:
        orm_mode = True


class UserModel(PrivateUserModel, PublicUserModel):
    class Config:
        orm_mode = True
