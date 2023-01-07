import logging
from typing import Union
from argon2 import PasswordHasher, exceptions
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.auth_details import PasswordError
from messenger.helpers.auth.is_email_valid import is_email_valid
from messenger.helpers.auth.is_password_valid import is_password_valid
from messenger.helpers.auth.is_username_valid import is_username_valid
from messenger.helpers.handlers.user_handler import UserHandler


logger = logging.getLogger(__name__)


password_hasher = PasswordHasher()


def authenticate_user(
    db: Session, password: str, email: str
) -> Union[UserSchema, bool]:
    """Authenticates a user using an email address and password.

    Args:
        db (Session): the database session to query with.
        password (str): a password used to verify whether the caller has authorization.
        email (str): an email address used to query the user from the database.

    Returns:
        Union[UserSchema, bool]: if the user does not exist or the password is not
        correct, return False. Otherwise return the database user.
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


def create_user(
    db: Session, password: str, email: str, username: str
) -> UserSchema:
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=email_validity_data.detail,
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
            detail=PasswordError.INVALID_PASSWORD.value,
        )

    password_hash = password_hasher.hash(password)
    user = UserSchema(
        username=username, password_hash=password_hash, email=email
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(
            "(user_id: %s) user has been successfully inserted into users table",
            user.user_id,
        )
    except SQLAlchemyError as exc:
        logger.error(
            "(user_id: %s) user was not inserted into users table due to %s",
            user.user_id,
            exc,
            exc_info=True,
        )

    return user
