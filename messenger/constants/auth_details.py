from enum import Enum


class EmailError(Enum):
    INVALID_EMAIL = "invalid email"
    ACCOUNT_EXISTS = "account already exists"


class UsernameError(Enum):
    INVALID_USERNAME = "invalid email"
    USERNAME_TAKEN = "username is taken"


class PasswordErro(Enum):
    INVALID_PASSWORD = "invalid password"
