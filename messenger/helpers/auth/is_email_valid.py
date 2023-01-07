"""Defines function(s) that validate an email"""

import re
from fastapi import HTTPException
from sqlalchemy.orm import Session

from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.auth_details import EmailError
from messenger.helpers.handlers.user_handler import UserHandler
from messenger.models.fastapi.validity_data import ValidityData


# Ensures emails entered are in the proper format ****@***.***
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"


def is_email_valid(db: Session, email: str) -> ValidityData:
    """Verifies whether an email is valid by format only

    Args:
        db (Session): the database session to query from
        email (str): the email whose format we will verify

    Returns:
        bool: whether the email format is valid
    """

    if re.match(EMAIL_PATTERN, email):
        user_handler = UserHandler(db)

        try:
            user_handler.get_user(UserSchema.email == email)
            return ValidityData(
                is_valid=False, detail=EmailError.ACCOUNT_EXISTS.value
            )
        except HTTPException:
            return ValidityData(is_valid=True, detail=None)

    return ValidityData(is_valid=False, detail=EmailError.INVALID_EMAIL.value)
