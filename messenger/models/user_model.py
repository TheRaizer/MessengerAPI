from datetime import datetime
from typing import Union
from pydantic import BaseModel

class UserBaseModel(BaseModel):
    email: str
    first_name: Union[str , None] = None
    last_name: Union[str , None] = None
    birthdate: Union[datetime , None] = None

class UserCreateModel(UserBaseModel):
    password: str


class UserModel(UserBaseModel):
    user_id: str
    username: str
    
    class Config:
        orm_mode = True
