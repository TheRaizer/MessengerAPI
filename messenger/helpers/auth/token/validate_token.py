from typing import Optional, Type
from jose import JWTError, jwt
from messenger.constants.token import ALGORITHM
from messenger.constants.generics import B


def validate_token(token: str, secret: str, TokenModel: Type[B]) -> Optional[B]:
    """Validates a given access token and if valid it decodes the token, and
    returns the decoded data. Otherwise it returns None.

    Args:
        token (str): the token to validate.
        secret (str): the secret used to validate the token.

    Returns:
        Optional[TokenData]: if token was valid, return the decoded data, otherwise
            return None
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        token_data = TokenModel(**payload)
    except JWTError:
        return None

    return token_data
