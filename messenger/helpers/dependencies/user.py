import logging
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.token import UNAUTHORIZED_CREDENTIALS_EXCEPTION
from messenger.settings import JWT_SECRET
from messenger.helpers.handlers.user_handler import UserHandler
from messenger.helpers.tokens.validate_token import (
    validate_token,
)
from messenger.helpers.tokens.auth_tokens import (
    oauth2_scheme,
    AccessTokenData,
)


logger = logging.getLogger(__name__)


password_hasher = PasswordHasher()


def get_current_user(
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
        db (Session, optional): The database session used for querying the user.
            Defaults to Depends(database_session).
        token (str, optional): a JWT token that represents the users credentials.
            Defaults to Depends(oauth2_scheme).

    Raises:
        UNAUTHORIZED_CREDENTIALS_EXCEPTION: An exception that returns a status of unauthorized.

    Returns:
        UserSchema: The users data from the database.
    """

    valid_token = validate_token(token, JWT_SECRET, AccessTokenData)

    if valid_token is None:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION

    user_handler = UserHandler(db)
    try:
        user = user_handler.get_user(
            UserSchema.email == valid_token.email,
        )

        return user
    except HTTPException as exc:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION from exc


def get_current_active_user(
    current_user: UserSchema = Depends(get_current_user),
) -> UserSchema:
    """Retrieves the currently active user using a given JWT token.
    Add as a dependency for routes that require authenticated users.

    Args:
        current_user (UserSchema, optional): the current user from the database,
        obtained using a JWT. Defaults to Depends(get_current_user).

    Returns:
        UserSchema: returns the currently active user.
    """

    return current_user
