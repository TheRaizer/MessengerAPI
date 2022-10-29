from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from messenger.helpers.auth import UNAUTHORIZED_CREDENTIALS_EXCEPTION, Token, create_login_token
from messenger.helpers.users import authenticate_user, create_user, get_db_user


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/sign-up", response_model=Token)
async def sign_up(username: str, form_data: OAuth2PasswordRequestFormStrict = Depends(), db: Session = Depends(database_session)):
    """Signs the user up, adding the required user data into the database and producing a JWT access token which
    the user can use to prove that they're authorized.

    Args:
        username (str): the username of the user to be signed up.
        form_data (OAuth2PasswordRequestFormStrict, optional): FastAPI's formdata that gives access to the user's email
        and password. Defaults to Depends().
        db (Session, optional): the database session used to add the new user. Defaults to Depends(database_session).

    Raises:
        HTTPException: A bad request if the user account already exists.

    Returns:
        Token: the access token and token type
    """
    user = get_db_user(db, email=form_data.username)
    
    if(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account exists",
        )
    
    # form_data.username represents the user's email
    user = create_user(db, password=form_data.password, email=form_data.username, username=username)
    
    access_token = create_login_token(user)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/sign-in", response_model=Token)
async def sign_in(form_data: OAuth2PasswordRequestFormStrict = Depends(), db: Session = Depends(database_session)):
    """Signs the user in using email and password authentication. Produces a JWT token proving the callers authorization.

    Args:
        form_data (OAuth2PasswordRequestFormStrict, optional): FastAPI's formdata that gives access to the user's email
        and password. Defaults to Depends().
        db (Session, optional): the database session used to query for a user. Defaults to Depends(database_session).

    Raises:
        UNAUTHORIZED_CREDENTIALS_EXCEPTION: returns an unauthorized access code when either the user authentication fails,
        or the user does not exist in the database.

    Returns:
        Token: the access token and token type
    """
    
    # form_data.username represents the user's email
    user = authenticate_user(db, password=form_data.password, email=form_data.username)
    
    if not user:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION
    
    access_token = create_login_token(user)
    
    
    return Token(access_token=access_token, token_type="bearer")

