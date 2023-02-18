"""Contains routes for messages."""

from datetime import date
from typing import Any, Callable, Optional, Type
from sqlalchemy import Column
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.generics import T
from messenger.helpers.dependencies.pagination import cursor_pagination
from messenger.helpers.dependencies.queries.query_messages import query_messages
from messenger.helpers.dependencies.user import get_current_active_user
from messenger.helpers.send_message import send_message
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
def send_message_route(
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
    return send_message(
        db, current_user, body.content, body.group_chat_id, addressee_username
    )
