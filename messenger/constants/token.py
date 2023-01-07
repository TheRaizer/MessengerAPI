from fastapi import HTTPException, status
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


ALGORITHM = "HS256"
LOGIN_TOKEN_EXPIRE_MINUTES = 30
UNAUTHORIZED_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
