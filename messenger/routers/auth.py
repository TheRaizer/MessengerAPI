"""Contains routes for user authentication."""
from datetime import timedelta
from bleach import clean
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.auth_details import EmailError
from messenger.constants.token import (
    LOGIN_TOKEN_EXPIRE_MINUTES,
    Token,
    UNAUTHORIZED_CREDENTIALS_EXCEPTION,
)
from messenger.helpers.tokens.auth_tokens import (
    create_access_token,
    create_login_token,
)

from messenger.helpers.handlers.user_handler import UserHandler
from messenger.helpers.auth.user import (
    authenticate_user,
    create_user,
)
from messenger.models.fastapi.socketio_access_token_data import (
    SocketioAccessTokenData,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.post(
    "/sign-up",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
)
def sign_up(
    username: str,
    form_data: OAuth2PasswordRequestFormStrict = Depends(),
    db: Session = Depends(database_session),
):
    """Signs the user up, adding the required user data into the database and
    producing a JWT access token which the user can use to prove that they're
    authorized.

    Args:
        username (str): the username of the user to be signed up.
        form_data (OAuth2PasswordRequestFormStrict, optional): FastAPI's formdata that
            gives access to the user's email and password. Defaults to Depends().
        db (Session, optional): the database session used to add the new user. Defaults
            to Depends(database_session).

    Raises:
        HTTPException: A bad request if the user account already exists.

    Returns:
        Token: the access token and token type
    """
    user_handler = UserHandler(db)

    try:
        user = user_handler.get_user(
            UserSchema.email == clean(form_data.username)
        )

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=EmailError.ACCOUNT_EXISTS.value,
            )
    except HTTPException:
        pass

    # form_data.username represents the user's email
    user = create_user(
        db,
        password=clean(form_data.password),
        email=clean(form_data.username),
        username=clean(username),
    )

    access_token = create_login_token(user)

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/sign-in",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
)
def sign_in(
    form_data: OAuth2PasswordRequestFormStrict = Depends(),
    db: Session = Depends(database_session),
):
    """Signs the user in using email and password authentication. Produces a
    JWT token proving the callers authorization.

    Args:
        form_data (OAuth2PasswordRequestFormStrict, optional): FastAPI's
            formdata that gives access to the user's email and password. Defaults
            to Depends().
        db (Session, optional): the database session used to query for a user.
            Defaults to Depends(database_session).

    Raises:
        UNAUTHORIZED_CREDENTIALS_EXCEPTION: returns an unauthorized access
        code when either the user authentication fails, or the user does not
        exist in the database.

    Returns:
        Token: the access token and token type
    """

    # form_data.username represents the user's email
    user = authenticate_user(
        db, password=clean(form_data.password), email=clean(form_data.username)
    )

    if not user:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION

    access_token = create_login_token(user)

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/socket-ticket", response_model=Token, status_code=status.HTTP_201_CREATED
)
def socket_ticket(
    form_data: OAuth2PasswordRequestFormStrict = Depends(),
    db: Session = Depends(database_session),
):
    """Using email and password authentication. Produces a
    JWT token proving the callers authorization for socket connection.

    Args:
        form_data (OAuth2PasswordRequestFormStrict, optional): FastAPI's
            formdata that gives access to the user's email and password. Defaults
            to Depends().
        db (Session, optional): the database session used to query for a user.
            Defaults to Depends(database_session).

    Raises:
        UNAUTHORIZED_CREDENTIALS_EXCEPTION: returns an unauthorized access
        code when either the user authentication fails, or the user does not
        exist in the database.

    Returns:
        Token: the access token and token type
    """

    # form_data.username represents the user's email
    user = authenticate_user(
        db, password=clean(form_data.password), email=clean(form_data.username)
    )

    if not user:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION

    socketio_token = create_access_token(
        SocketioAccessTokenData(user_id=user.user_id),
        timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=socketio_token, token_type="socketio")
