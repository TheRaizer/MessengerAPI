"""Defines function(s) that validate a username"""

import re
from fastapi import HTTPException
from sqlalchemy.orm import Session

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.auth_details import UsernameError
from messenger.helpers.auth import ValidityData
from messenger.helpers.user_handler import UserHandler

"""
Rules username regex enforces:
    1. No '_' or '.' at the end
    2. Only lowercase, uppercase, digits, '_' and '.' characters are allowed
    3. No '__' or '_.' or '._' or '..' inside
    4. No '_' or '.' at the beginning
 */
"""
USERNAME_PATTERN = r"^(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$"


def is_username_valid(db: Session, username: str) -> ValidityData:
    """Verifies whether a username is valid.

    Rules for an acceptable username:
        1. No '_' or '.' at the end or beginning
        2. Only lowercase, uppercase, digits, '_' and '.' characters are allowed
        3. No '__' or '_.' or '._' or '..' inside
        4. must have a length between 3 and 25 inclusive.

    Args:
        db (Session): the database session to query from
        username (str): the username to verify for validity

    Returns:
        bool: whether the username is valid
    """

    if (
        re.match(USERNAME_PATTERN, username)
        and len(username) >= 3
        and len(username) <= 25
    ):
        user_handler = UserHandler(db)

        try:
            # if user exists with this username no HTTPException is thrown
            user_handler.get_user(UserSchema.username == username)
            return ValidityData(
                is_valid=False, detail=UsernameError.USERNAME_TAKEN.value
            )
        except HTTPException:
            return ValidityData(is_valid=True, detail=None)

    return ValidityData(
        is_valid=False, detail=UsernameError.INVALID_USERNAME.value
    )
