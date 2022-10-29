from datetime import datetime, timedelta
from typing import Union
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema


SECRET_KEY = "ba69af06511d1881bd552bbe131e5452c98df8ee97dc2a893215f8a2e3d44e4a"
ALGORITHM = "HS256"
LOGIN_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign-in")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Union[str, None] = None
    username: Union[str, None] = None
    email: Union[str, None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UNAUTHORIZED_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies whether a hashed password's original value is equal to a given plain text password.

    Args:
        plain_password (str): a plain text password.
        hashed_password (str): a hashed password.

    Returns:
        bool: whether a hashed password's original value is equal to a given plain text password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """A password must be stored as a hash in the database. This function hashes a password
    using bcrypt which will produce a CHAR(60) data type to be stored in the database.

    Args:
        password (str): the password to hash.

    Returns:
        str: the hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Creates a JWT access token that can expire.

    Args:
        data (dict): the data to be encrypted into the token.
        expires_delta (Union[timedelta, None], optional): The amount of time before 
        the token should expire. Defaults to None.

    Returns:
        str: an encoded JWT access token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def create_login_token(user: UserSchema) -> str:
    """Create a new login token that will be used to authorize the user and label them as logged in.

    Args:
        user (UserSchema): The users data from the database.

    Returns:
        str: the access token in the form of a JWT.
    """
    token_data: TokenData = TokenData(**(user.__dict__))
    access_token_expires = timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data=token_data.dict(), expires_delta=access_token_expires
    )
    
    return access_token