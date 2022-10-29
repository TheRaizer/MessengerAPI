from typing import Union
from fastapi import Depends
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.auth import ALGORITHM, UNAUTHORIZED_CREDENTIALS_EXCEPTION, SECRET_KEY, TokenData, get_password_hash, verify_password
from messenger.helpers.auth import oauth2_scheme



def get_db_user(db: Session, email: str) -> Union[UserSchema, None]:
    """Returns the first instance of a database user by matching it to an email address, or 
    None if noe user is found.

    Args:
        db (Session): a database session to use for queries.
        email (str): an email address used to find a user.

    Returns:
        Union[UserSchema, None]: the user found in the database, or None if no user is found.
    """
    user: Union[UserSchema, None] = db.query(UserSchema).filter_by(email=email).first()
    return user

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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        
        if payload.get('email') is None:
            raise UNAUTHORIZED_CREDENTIALS_EXCEPTION
        token_data = TokenData(**payload)
        
    except JWTError:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION
    
    user = get_db_user(db, token_data.email)
    
    if user is None:
        raise UNAUTHORIZED_CREDENTIALS_EXCEPTION
    
    return user


async def get_current_active_user(current_user: UserSchema = Depends(get_current_user)):
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
    user = get_db_user(db, email)
    
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    
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
    # TODO: create helper function to ensure password is valid
    # TODO: Create helper function to ensure username is valid
    # TODO: create helper function to ensure email is valid
    password_hash = get_password_hash(password)
    user = UserSchema(username=username, password_hash=password_hash, email=email)
    
    # TODO: seperate this logic into its own function
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

