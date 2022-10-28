from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.engine import database_session
from messenger.helpers.auth import ACCESS_TOKEN_EXPIRE_MINUTES, Token, TokenData, create_access_token
from messenger.helpers.users import authenticate_user, create_user, get_db_user


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/sign-up", response_model=Token)
async def sign_up(username: str, form_data: OAuth2PasswordRequestFormStrict = Depends(), db: Session = Depends(database_session)):
    user = get_db_user(db, email=form_data.username)
    
    if(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account exists",
        )
    
    user = create_user(db, password=form_data.password, email=form_data.username, username=username)
    
    tokenData: TokenData = TokenData(**(user.__dict__))
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data=tokenData.dict(), expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
    

@router.post("/sign-in", response_model=Token)
async def sign_in(form_data: OAuth2PasswordRequestFormStrict = Depends(), db: Session = Depends(database_session)):
    user = authenticate_user(db, password=form_data.password, email=form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    tokenData: TokenData = TokenData(**(user.__dict__))
    
    access_token = create_access_token(
        data=tokenData.dict(), expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

