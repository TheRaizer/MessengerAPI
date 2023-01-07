"""Defines the GroupChatHandler class"""

from typing import Optional
from sqlalchemy.orm import Session
from messenger_schemas.schema.group_chat_member_schema import (
    GroupChatMemberSchema,
)
from messenger_schemas.schema.group_chat_schema import (
    GroupChatSchema,
)
from messenger.helpers.handlers.database_handler import DatabaseHandler


class GroupChatHandler(DatabaseHandler):
    """Handles manipulation of groupchat database records"""

    def __init__(
        self, db: Session, group_chat: Optional[GroupChatSchema] = None
    ):
        super().__init__(db)
        self.group_chat = group_chat

    def is_user_in_group_chat(self, group_chat_id: int, user_id: int) -> bool:
        """Returns whether the user is in a given group chat or not.

        Args:
            group_chat_id (int): the id of the group chat that we will attempt
                to find the user in.
            user_id (int): the id of the user that we will attempt to find in a
                group chat.

        Returns:
            bool: whether the user is in the group chat
        """

        record = self._get_record(
            GroupChatMemberSchema,
            GroupChatMemberSchema.c.group_chat_id == group_chat_id,
            GroupChatMemberSchema.c.member_id == user_id,
        )

        return record is not None

    def get_group_chat(self, *criterion) -> GroupChatSchema:
        """Retrieves a group chat. Throws an error if no group chat was found.

        Returns:
            GroupChatSchema: the group chat that was found.
        """
        self.group_chat = self._get_record_with_not_found_raise(
            GroupChatSchema, "no such group chat exists", *criterion
        )

        return self.group_chat
