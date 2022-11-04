from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserBaseModel(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[datetime] = None

class UserCreateModel(UserBaseModel):
    password: str


class UserModel(UserBaseModel):
    user_id: str
    username: str
    
    class Config:
        orm_mode = True
