from datetime import datetime, timedelta
from typing import Union
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.token import (
    ALGORITHM,
    LOGIN_TOKEN_EXPIRE_MINUTES,
)
from messenger.constants.generics import B
from messenger.models.fastapi.access_token_data import AccessTokenData
from messenger.settings import JWT_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign-in")


def create_access_token(
    data: B, expires_delta: Union[timedelta, None] = None
) -> str:
    """Creates a JWT access token that can expire.

    Args:
        data (dict): the data to be encrypted into the token.
        expires_delta (Union[timedelta, None], optional): The amount of time before
        the token should expire. Defaults to None.

    Returns:
        str: an encoded JWT access token.
    """
    to_encode = data.dict().copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

    return encoded_jwt


def create_login_token(user: UserSchema):
    return create_access_token(
        AccessTokenData(
            user_id=user.user_id, username=user.username, email=user.email
        ),
        timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES),
    )
