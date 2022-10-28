from datetime import datetime
from typing import Union
from pydantic import BaseModel

class UserBaseModel(BaseModel):
    email: str
    firstName: Union[str , None] = None
    lastName: Union[str , None] = None
    birthDate: Union[datetime , None] = None

class UserCreateModel(UserBaseModel):
    password: str


class UserModel(UserBaseModel):
    userId: str
    username: str
    
    class Config:
        orm_mode = True