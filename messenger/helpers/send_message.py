from typing import Optional
from bleach import clean
from fastapi import HTTPException, status
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from sqlalchemy.orm import Session
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.helpers.handlers.friendship_handler import FriendshipHandler
from messenger.helpers.handlers.group_chat_handler import GroupChatHandler
from messenger.helpers.handlers.message_handler import MessageHandler
from messenger.helpers.handlers.user_handler import UserHandler
from messenger.models.fastapi.message_model import MessageModel


def send_message(
    db: Session,
    current_user_id: int,
    content: str,
    group_chat_id: Optional[int] = None,
    addressee_username: Optional[str] = None,
) -> MessageModel:
    addressee_handler = UserHandler(db)

    if group_chat_id is not None:
        group_chat_handler = GroupChatHandler(db)

        if not group_chat_handler.is_user_in_group_chat(
            group_chat_id, current_user_id
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    elif addressee_username is not None:
        addressee = addressee_handler.get_user(
            UserSchema.username == clean(addressee_username),
        )

        friendship_handler = FriendshipHandler(db)

        friendship_handler.get_friendship_bidirectional_query(
            current_user_id, addressee.user_id
        )

        latest_status = friendship_handler.get_latest_friendship_status()

        # friendship must be accepted
        if (
            latest_status is None
            or latest_status.status_code_id
            != FriendshipStatusCode.ACCEPTED.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you cannot message this person if you are not their friend",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no addressee or groupchat specified",
        )

    message_handler = MessageHandler(db)

    message = message_handler.send_message(
        current_user_id,
        getattr(addressee_handler.user, "user_id", None),
        content,
        group_chat_id,
    )

    message_model = MessageModel.from_orm(message)

    return message_model
