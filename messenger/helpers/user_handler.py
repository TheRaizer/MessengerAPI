"""Defines the UserHandler class."""

from typing import Optional
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.helpers.db import DatabaseHandler


class UserHandler(DatabaseHandler):
    """Allows access to basic user utility methods."""

    def __init__(self, db: Session, user: Optional[UserSchema] = None):
        super().__init__(db)
        self.user = user

    def get_user(self, *criterion) -> UserSchema:
        self.user = self._get_record_with_not_found_raise(
            UserSchema, "no such user exists", *criterion
        )

        return self.user
