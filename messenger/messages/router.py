from typing import List
from bleach import clean
from fastapi import APIRouter, Depends, HTTPException, status
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.friends.friendship_handler import FriendshipHandler
from messenger.helpers.group_chat import GroupChatHandler
from messenger.messages.message_handler import MessageHandler
from messenger.helpers.user_handler import UserHandler
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
    addressee_handler = UserHandler(db)
    addressee = None

    if body.group_chat_id:
        group_chat_handler = GroupChatHandler(db)

        if not group_chat_handler.is_user_in_group_chat(
            body.group_chat_id, current_user
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    else:
        addressee = addressee_handler.get_user(
            UserSchema.username == clean(addressee_username),
        )

        friendship_handler = FriendshipHandler(db)
        friendship_handler.get_friendship_bidirectional_query(current_user, addressee)

        latest_status = friendship_handler.get_latest_friendship_status()
        # friendship must be accepted
        if (
            latest_status is None
            or latest_status != FriendshipStatusCode.ACCEPTED.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=must_be_their_friend_detail,
            )

    message_handler = MessageHandler(db)
    message = message_handler.send_message(
        current_user.user_id,
        getattr(addressee, "user_id", None),
        body.content,
        getattr(body, "group_chat_id", None),
    )

    message_model = BaseMessageModel(
        content=message.content,
        group_chat_id=message.group_chat_id,
        created_date_time=message.created_date_time,
        last_edited_date_time=message.last_edited_date_time,
        seen=message.seen,
    )

    return message_model
