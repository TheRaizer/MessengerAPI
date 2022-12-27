"""Defines functions related to authentication tokens"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from argon2 import PasswordHasher
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.settings import JWT_SECRET

ALGORITHM = "HS256"
LOGIN_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign-in")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None


password_hasher = PasswordHasher()

UNAUTHORIZED_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def validate_access_token(token: str, secret: str) -> Optional[TokenData]:
    """Validates a given access token and if valid it decodes the token, and
    returns the decoded data. Otherwise it returns None.

    Args:
        token (str): the token to validate.
        secret (str): the secret used to validate the token.

    Returns:
        Optional[TokenData]: if token was valid, return the decoded data, otherwise
            return None
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        token_data = TokenData(**payload)

    except JWTError:
        return None

    return token_data


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


def create_login_token(user: UserSchema) -> str:
    """Create a new login token that will be used to authorize the user and label them as logged in.

    Args:
        user (UserSchema): The users data from the database.

    Returns:
        str: the access token in the form of a JWT.
    """
    token_data: TokenData = TokenData(
        user_id=user.user_id, username=user.username, email=user.email
    )
    access_token_expires = timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data=token_data.dict(), expires_delta=access_token_expires
    )

    return access_token
