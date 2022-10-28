from typing import Union
from fastapi import Depends
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.engine import database_session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.auth import ALGORITHM, CREDENTIALS_EXCEPTION, SECRET_KEY, TokenData, get_password_hash, verify_password
from messenger.helpers.auth import oauth2_scheme



def get_db_user(db: Session, email: str) -> Union[UserSchema, None]:
    user: Union[UserSchema, None] = db.query(UserSchema).filter_by(email=email).first()
    return user

async def get_current_user(db: Session = Depends(database_session), token: str = Depends(oauth2_scheme)) -> UserSchema:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        
        if payload.get('email') is None or payload.get('userId') is None or payload.get('username') is None:
            raise CREDENTIALS_EXCEPTION
        token_data = TokenData(**payload)
        
    except JWTError:
        raise CREDENTIALS_EXCEPTION
    
    user = get_db_user(db, token_data.email)
    
    if user is None:
        raise CREDENTIALS_EXCEPTION
    
    return user


async def get_current_active_user(current_user: UserSchema = Depends(get_current_user)):
    return current_user


def authenticate_user(db: Session, password: str, email: str) -> Union[UserSchema, bool]:
    user = get_db_user(db, email)
    
    if not user:
        return False
    if not verify_password(password, user.passwordHash):
        return False
    
    return user

def create_user(db: Session, password: str, email: str, username: str) -> UserSchema:
    # TODO: create helper function to ensure password is valid
    # TODO: Create helper function to ensure username is valid
    # TODO: create helper function to ensure email is valid
    passwordHash = get_password_hash(password)
    user = UserSchema(username=username, passwordHash=passwordHash, email=email)
    
    # TODO: seperate this logic into its own function
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user