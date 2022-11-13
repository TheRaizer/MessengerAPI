from datetime import datetime
from typing import List, Optional
from bleach import clean
from fastapi import APIRouter, Depends, HTTPException, status
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_member_schema import (
    GroupChatMemberSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.message_schema import (
    MessageSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.helpers.db import DatabaseHandler
from messenger.helpers.friends import FriendshipHandler
from messenger.helpers.users import get_current_active_user
from sqlalchemy.orm import Session
from messenger.models.message_model import BaseMessageModel, CreateMessageModel


router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/", response_model=List[BaseMessageModel], status_code=status.HTTP_200_OK)
def get_messages(current_user: UserSchema = Depends(get_current_active_user)):
    message_models = list(
        map(
            lambda message_schema: BaseMessageModel(
                content=message_schema.content,
                group_chat_id=message_schema.group_chat_id,
                created_date_time=message_schema.created_date_time,
                last_edited_date_time=message_schema.last_edited_date_time,
                seen=message_schema.seen,
            ),
            current_user.messages_recieved,
        )
    )
    return message_models


@router.post("/", response_model=BaseMessageModel, status_code=status.HTTP_201_CREATED)
def send_message(
    addressee_username: str,
    body: CreateMessageModel,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    must_be_their_friend_detail = (
        "you cannot message this person if you are not their friend"
    )
    """Sends a message from the currently signed in user to either another user, or a group chat.
    
    If a group chat id is specified, we will send a message to a group chat, otherwise we will send it to a specified addressee.

    Args:
        addressee_username (str): the username of the user to send a message too.
        current_user (UserSchema, optional): The current user that will represent the sender of the message.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to data from and post data too.
        Defaults to Depends(database_session).

    Returns:
        OKModel: whether the message was successfully sent
    """

    database_handler = DatabaseHandler(db)
    addressee: Optional[UserSchema] = None

    if body.group_chat_id:
        # ensure that a db record connecting this user and the group chat exists
        database_handler._get_record_with_not_found_raise(
            GroupChatMemberSchema,
            "not a member of this groupchat",
            GroupChatMemberSchema.group_chat_id == body.group_chat_id,
            GroupChatMemberSchema.member_id == current_user.user_id,
        )
    else:
        addressee = database_handler._get_record_with_not_found_raise(
            UserSchema,
            "addressee with the given username does not exist",
            UserSchema.username == clean(addressee_username),
        )

        friendship_service = FriendshipHandler(db)
        friendship_service.get_friendship_bidirectional_query(current_user, addressee)

        # friendship must be accepted
        if (
            friendship_service.friendship is None
            or friendship_service.get_latest_friendship_status().status_code_id
            != FriendshipStatusCode.ACCEPTED.value
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=must_be_their_friend_detail,
            )

    message = MessageSchema(
        sender_id=current_user.user_id,
        reciever_id=getattr(addressee, "user_id", None),
        content=body.content,
        created_date_time=datetime.now(),
        group_chat_id=getattr(body, "group_chat_id", None),
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    message_model = BaseMessageModel(
        content=message.content,
        group_chat_id=message.group_chat_id,
        created_date_time=message.created_date_time,
        last_edited_date_time=message.last_edited_date_time,
        seen=message.seen,
    )

    return message_model
