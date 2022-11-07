from datetime import datetime, timedelta
from typing import Optional, Union
from jose import jwt
from argon2 import PasswordHasher
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
import re
from sqlalchemy.orm import Session

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.db import get_record

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
        
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    
    return encoded_jwt

def create_login_token(user: UserSchema) -> str:
    """Create a new login token that will be used to authorize the user and label them as logged in.

    Args:
        user (UserSchema): The users data from the database.

    Returns:
        str: the access token in the form of a JWT.
    """
    token_data: TokenData = TokenData(user_id=user.user_id, username=user.username, email=user.email)
    access_token_expires = timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data=token_data.dict(), expires_delta=access_token_expires
    )
    
    return access_token


def is_password_valid(password: str) -> bool:
    """Verifies whether a password is valid.

    Args:
        password (str): Password to verify.

    Returns:
        bool: whether the password is valid.
    """
    rules = [lambda password: any(char.isupper() for char in password), # must have at least one uppercase
        lambda password: any(char.islower() for char in password),  # must have at least one lowercase
        lambda password: any(char.isdigit() for char in password),  # must have at least one digit
        lambda password: len(password) >= 8                # must be at least 8 characters
        ]
    
    # apply each rule to the password and ensure that all are true
    if all(rule(password) for rule in rules):
        return True
    
    return False


"""
Rules username regex enforces:
    1. No '_' or '.' at the end
    2. Only lowercase, uppercase, digits, '_' and '.' characters are allowed
    3. No '__' or '_.' or '._' or '..' inside
    4. No '_' or '.' at the beginning
 */
"""
USERNAME_PATTERN = r"^(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$"

def is_username_valid(db: Session, username: str) -> bool:
    """Verifies whether a username is valid.

    Rules for an acceptable username:
        1. No '_' or '.' at the end
        2. Only lowercase, uppercase, digits, '_' and '.' characters are allowed
        3. No '__' or '_.' or '._' or '..' inside
        4. No '_' or '.' at the beginning
        5. must have a length between 3 and 25 inclusive.
    
    Args:
        db (Session): the database session to query from
        username (str): the username to verify for validity

    Returns:
        bool: whether the username is valid
    """
    
    
    if(re.match(USERNAME_PATTERN, username) and len(username) >= 3 and len(username) <= 25):
        user_record = get_record(db, UserSchema, UserSchema.username == username)
        
        return user_record is None
    
    return False

# Ensures emails entered are in the proper format ****@***.***
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

def is_email_valid(db: Session, email: str) -> bool:
    """Verifies whether an email is valid by format only

    Args:
        db (Session): the database session to query from
        email (str): the email whose format we will verify

    Returns:
        bool: whether the email format is valid
    """
    
    if(re.match(EMAIL_PATTERN, email)):
        user_record = get_record(db, UserSchema, UserSchema.email == email)
    
        return user_record is None
    
    return False