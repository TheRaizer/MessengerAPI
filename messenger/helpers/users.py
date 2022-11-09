from typing import Union
from argon2 import exceptions
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth import ALGORITHM, UNAUTHORIZED_CREDENTIALS_EXCEPTION, TokenData
from messenger.helpers.auth import oauth2_scheme
from messenger.helpers.db import get_record, get_record_with_not_found_raise
from .auth import is_email_valid, is_password_valid, is_username_valid, password_hasher

async def get_current_user(db: Session = Depends(database_session), token: str = Depends(oauth2_scheme)) -> UserSchema:
    """Retrieves a user's data from the database using a given JWT token.

        IF
            JWT cannot be decoded
            OR
            no user can be found using the JWT's email address value
        THEN
            throw unauthorized exception.

    Args:
        db (Session, optional): The database session used for querying the user. Defaults to Depends(database_session).
        token (str, optional): a JWT token that represents the users credentials. Defaults to Depends(oauth2_scheme).

    Raises:
        UNAUTHORIZED_CREDENTIALS_EXCEPTION: An exception that returns a status of unauthorized.

    Returns:
        UserSchema: The users data from the database.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        
        
        if payload.get('email') is None:
            raise UNAUTHORIZED_CREDENTIALS_EXCEPTION
        token_data = TokenData(**payload)
        
    except JWTError:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION
    
    user = get_record_with_not_found_raise(db, UserSchema, "user credentials are invalid", UserSchema.email == token_data.email)
    
    return user


async def get_current_active_user(current_user: UserSchema = Depends(get_current_user)) -> UserSchema:
    """Retrieves the currently active user using a given JWT token.
    Add as a dependency for routes that require authenticated users.

    Args:
        current_user (UserSchema, optional): the current user from the database, obtained using a JWT. Defaults to Depends(get_current_user).

    Returns:
        UserSchema: returns the currently active user.
    """
    return current_user


def authenticate_user(db: Session, password: str, email: str) -> Union[UserSchema, bool]:
    """Authenticates a user using an email address and password.

    Args:
        db (Session): the database session to query with.
        password (str): a password used to verify whether the caller has authorization.
        email (str): an email address used to query the user from the database.

    Returns:
        Union[UserSchema, bool]: if the user does not exist or the password is not correct, return False.
        Otherwise return the database user.
    """
    user = get_record(db, UserSchema, UserSchema.email==email)
    
    if not user:
        return False
    
    try:
        password_hasher.verify(user.password_hash, password)
    except exceptions.VerifyMismatchError:
        # If verification fails because *hash* is not valid for *password*.
        return False
    except exceptions.VerificationError:
        # If there is another reason that verification failed
        return False
    except exceptions.InvalidHash:
        # If the hash is so unbelievably invalid it cannot be passed to argon2
        return False
    
    # if user's password needs a rehash do it here
    if(password_hasher.check_needs_rehash(user.password_hash)):
        user.password_hash = password_hasher.hash(password)
        db.refresh(user)
    
    return user


def create_user(db: Session, password: str, email: str, username: str) -> UserSchema:
    """Creates a user in the database.

    Args:
        db (Session): the database session to use for the creation of the user.
        password (str): a password whose hash will be stored in the database.
        email (str): an email address to store in the database.
        username (str): a username to store in the database.

    Returns:
        UserSchema: the user that was created in the database.
    """
    if(not is_password_valid(password)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid password")
    if(not is_username_valid(db, username)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid username")
    if(not is_email_valid(db, email)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid email")
    
    password_hash = password_hasher.hash(password)
    user = UserSchema(username=username, password_hash=password_hash, email=email)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

