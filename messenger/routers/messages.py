"""Contains routes for messages."""

from datetime import date
from typing import Any, Callable, Optional, Type
from bleach import clean
from sqlalchemy import Column
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.constants.generics import T
from messenger.helpers.dependencies.pagination import cursor_pagination
from messenger.helpers.dependencies.queries.query_messages import query_messages
from messenger.helpers.handlers.friendship_handler import FriendshipHandler
from messenger.helpers.handlers.group_chat_handler import GroupChatHandler
from messenger.helpers.handlers.message_handler import MessageHandler
from messenger.helpers.handlers.user_handler import UserHandler
from messenger.helpers.dependencies.user import get_current_active_user
from messenger.models.fastapi.message_model import (
    BaseMessageModel,
    CreateMessageModel,
)
from messenger.models.fastapi.pagination_model import CursorPaginationModel


router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=CursorPaginationModel[BaseMessageModel],
    status_code=status.HTTP_200_OK,
)
def get_messages(
    pagination: Callable[
        [Type[T], Column, Any],
        CursorPaginationModel,
    ] = Depends(cursor_pagination),
    messages_table=Depends(query_messages),
):
    """Returns all messages this user has recieved.

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).

    Returns:
        CursorPaginationModel[BaseMessageModel]: the messages this user has recieved
    """

    cursor_pagination_model = pagination(
        messages_table,
        messages_table.created_date_time,
        date(2019, 4, 13),
    )

    cursor_pagination_model.results = [
        BaseMessageModel.from_orm(message)
        for message in cursor_pagination_model.results
    ]

    return cursor_pagination_model


@router.post(
    "/", response_model=BaseMessageModel, status_code=status.HTTP_201_CREATED
)
def send_message(
    addressee_username: Optional[str],
    body: CreateMessageModel,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Sends a message from the currently signed in user to either another user, or a group chat.

    If a group chat id is specified, we will send a message to a group chat, otherwise we will
    send it to a specified addressee.

    Args:
        addressee_username (str): the username of the user to send a message too.
        current_user (UserSchema, optional): The current user that will represent the sender
            of the message. Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to data from and post data too.
            Defaults to Depends(database_session).

    Returns:
        OKModel: whether the message was successfully sent
    """
    addressee_handler = UserHandler(db)

    if body.group_chat_id is not None:
        group_chat_handler = GroupChatHandler(db)

        if not group_chat_handler.is_user_in_group_chat(
            body.group_chat_id, current_user.user_id
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    elif addressee_username is not None:
        addressee = addressee_handler.get_user(
            UserSchema.username == clean(addressee_username),
        )

        friendship_handler = FriendshipHandler(db)

        friendship_handler.get_friendship_bidirectional_query(
            current_user.user_id, addressee.user_id
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
        current_user.user_id,
        getattr(addressee_handler.user, "user_id", None),
        body.content,
        getattr(body, "group_chat_id", None),
    )

    message_model = BaseMessageModel.from_orm(message)

    return message_model
