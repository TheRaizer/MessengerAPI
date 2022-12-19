"""Defines the MessageHandler class"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from messenger_schemas.schema.message_schema import (
    MessageSchema,
)
from messenger.helpers.db import DatabaseHandler


class MessageHandler(DatabaseHandler):
    """Contains methods that allow manipulation of messages"""

    def __init__(self, db: Session, message: Optional[MessageSchema] = None):
        super().__init__(db)
        self.message = message

    def send_message(
        self,
        sender_id: Optional[int],
        reciever_id: Optional[int],
        content: str,
        group_chat_id: Optional[int],
    ) -> MessageSchema:
        """Sends a message from one user to another.

        Args:
            sender_id (Optional[int]): the user_id of the user sending the message.
            reciever_id (Optional[int]): the user_id of the user recieving this message
            content (str): the content of the message
            group_chat_id (Optional[int]): the group chat id that this message may be apart of.

        Returns:
            MessageSchema: _description_
        """

        message = MessageSchema(
            sender_id=sender_id,
            reciever_id=reciever_id,
            content=content,
            created_date_time=datetime.now(),
            group_chat_id=group_chat_id,
        )

        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)

        return message

    def get_message(self, *criterion) -> MessageSchema:
        """Retrieves a message given a set of criterion.
        If no message is found an exception is raised.

        Returns:
            MessageSchema: the message that was retrieved.
        """

        self.message = self._get_record_with_not_found_raise(
            MessageSchema, "no such message exists", *criterion
        )

        return self.message
