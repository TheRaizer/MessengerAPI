from typing import Optional
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_member_schema import (
    GroupChatMemberSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_schema import (
    GroupChatSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.db import DatabaseHandler
from sqlalchemy.orm import Session


class GroupChatHandler(DatabaseHandler):
    def __init__(self, db: Session, group_chat: Optional[GroupChatSchema] = None):
        super().__init__(db)
        self.group_chat = group_chat

    def is_user_in_group_chat(self, group_chat_id: int, user: UserSchema) -> bool:
        record = self._get_record(
            GroupChatMemberSchema,
            GroupChatMemberSchema.group_chat_id == group_chat_id,
            GroupChatMemberSchema.member_id == user.user_id,
        )

        return record is not None

    def get_group_chat(self, *criterion):
        self.group_chat = self._get_record_with_not_found_raise(
            GroupChatSchema, "no such group chat exists", *criterion
        )

        return self.group_chat
