from messenger.helpers.db import DatabaseHandler
from typing import Optional
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema


class UserHandler(DatabaseHandler):
    def __init__(self, db: Session, user: Optional[UserSchema] = None):
        super().__init__(db)
        self.user = user

    def get_user(self, *criterion):
        self.user = self._get_record_with_not_found_raise(
            UserSchema, "no such user exists", *criterion
        )

        return self.user
