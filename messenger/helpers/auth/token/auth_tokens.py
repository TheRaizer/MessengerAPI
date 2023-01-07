"""Defines functions related to authentication tokens"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import jwt
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.token import (
    ALGORITHM,
    LOGIN_TOKEN_EXPIRE_MINUTES,
)
from messenger.settings import JWT_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign-in")


class SocketioAccessTokenData(BaseModel):
    user_id: Optional[str] = None
    type: str = "socket"


class AccessTokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None


def create_access_token(
    data: dict, expires_delta: Union[timedelta, None] = None
) -> str:
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
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

    return encoded_jwt


def create_socketio_token(user: UserSchema) -> str:
    """Create a ticket for authentication during socketio connection.

    Args:
        user (UserSchema): The users data from the database.

    Returns:
        str: the token in the form of a JWT.
    """
    token_data: SocketioAccessTokenData = SocketioAccessTokenData(
        user_id=user.user_id,
    )
    access_token_expires = timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data=token_data.dict(), expires_delta=access_token_expires
    )

    return access_token


def create_login_token(user: UserSchema) -> str:
    """Create a new login token that will be used to authorize the user and label them as logged in.

    Args:
        user (UserSchema): The users data from the database.

    Returns:
        str: the access token in the form of a JWT.
    """
    token_data: AccessTokenData = AccessTokenData(
        user_id=user.user_id, username=user.username, email=user.email
    )
    access_token_expires = timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data=token_data.dict(), expires_delta=access_token_expires
    )

    return access_token
