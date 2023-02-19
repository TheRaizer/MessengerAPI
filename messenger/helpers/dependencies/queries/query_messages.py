from bleach import clean
from fastapi import Depends
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, aliased
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger_schemas.schema.message_schema import (
    MessageSchema,
)
from messenger.helpers.dependencies.user import get_current_active_user
from messenger.helpers.handlers.user_handler import UserHandler


def query_messages(
    friend_username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Produces a subquery table of all messages between the sender and the current user.

    SELECT * FROM message WHERE sender_id={...} and reciever_id={current_user.user_id}

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to query from.
            Defaults to Depends(database_session).
    """

    sender_handler = UserHandler(db)
    sender = sender_handler.get_user(
        UserSchema.username == clean(friend_username),
    )

    filter_a = and_(
        MessageSchema.sender_id == sender.user_id,
        MessageSchema.reciever_id == current_user.user_id,
    ).self_group()
    filter_b = and_(
        MessageSchema.sender_id == current_user.user_id,
        MessageSchema.reciever_id == sender.user_id,
    ).self_group()

    messages_table = (
        db.query(MessageSchema)
        .filter(
            or_(
                *[
                    filter_a,
                    filter_b,
                ]
            )
        )
        .subquery()
    )

    messages_table_alias = aliased(MessageSchema, messages_table)

    return messages_table_alias
