from datetime import datetime
from typing import Optional
from _submodules.messenger_utils.messenger_schemas.schema.message_schema import (
    MessageSchema,
)
from messenger.helpers.db import DatabaseHandler
from sqlalchemy.orm import Session


class MessageHandler(DatabaseHandler):
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

    def get_message(self, *criterion):
        self.message = self._get_record_with_not_found_raise(
            MessageSchema, "no such message exists", criterion
        )

        return self.message
