import logging
from typing import Union
from argon2 import exceptions
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.constants.auth_details import PasswordErro
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth.is_email_valid import is_email_valid
from messenger.helpers.auth.is_password_valid import is_password_valid
from messenger.helpers.auth.is_username_valid import is_username_valid
from .auth.auth_token import oauth2_scheme
from messenger.helpers.user_handler import UserHandler
from .auth.auth_token import (
    password_hasher,
    validate_access_token,
    UNAUTHORIZED_CREDENTIALS_EXCEPTION,
)


logger = logging.getLogger(__name__)


async def get_current_user(
    db: Session = Depends(database_session), token: str = Depends(oauth2_scheme)
) -> UserSchema:
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
    valid_token = validate_access_token(token, JWT_SECRET)

    if valid_token is None:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION

    user_handler = UserHandler(db)
    try:
        user = user_handler.get_user(
            UserSchema.email == valid_token.email,
        )

        return user
    except HTTPException:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION


async def get_current_active_user(
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    """Retrieves the currently active user using a given JWT token.
    Add as a dependency for routes that require authenticated users.

    Args:
        current_user (UserSchema, optional): the current user from the database, obtained using a JWT. Defaults to Depends(get_current_user).

    Returns:
        UserSchema: returns the currently active user.
    """
    return current_user


def authenticate_user(
    db: Session, password: str, email: str
) -> Union[UserSchema, bool]:
    """Authenticates a user using an email address and password.

    Args:
        db (Session): the database session to query with.
        password (str): a password used to verify whether the caller has authorization.
        email (str): an email address used to query the user from the database.

    Returns:
        Union[UserSchema, bool]: if the user does not exist or the password is not correct, return False.
        Otherwise return the database user.
    """

    user_handler = UserHandler(db)

    user = user_handler.get_user(UserSchema.email == email)

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
    if password_hasher.check_needs_rehash(user.password_hash):
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

    # check if email is valid or exists
    email_validity_data = is_email_valid(db, email)
    if not email_validity_data.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=email_validity_data.detail
        )

    # check if username is valid or taken
    username_validity_data = is_username_valid(db, username)
    if not username_validity_data.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=username_validity_data.detail,
        )

    if not is_password_valid(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=PasswordErro.INVALID_PASSWORD.value,
        )

    password_hash = password_hasher.hash(password)
    user = UserSchema(username=username, password_hash=password_hash, email=email)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(
            "(user_id: %s) user has been successfully inserted into users table",
            user.user_id,
        )
    except Exception as e:
        logger.error(
            "(user_id: %s) user was not inserted into users table due to %s",
            user.user_id,
            e,
            exc_info=True,
        )

    return user
