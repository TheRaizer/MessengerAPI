"""Detail/Error enums that are used in validation of email, username, and password"""

from enum import Enum


class EmailError(Enum):
    INVALID_EMAIL = "invalid email"
    ACCOUNT_EXISTS = "account already exists"


class UsernameError(Enum):
    INVALID_USERNAME = "invalid username"
    USERNAME_TAKEN = "username is taken"


class PasswordError(Enum):
    INVALID_PASSWORD = "invalid password"
