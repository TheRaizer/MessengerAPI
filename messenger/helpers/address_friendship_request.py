from typing import Literal

from fastapi import HTTPException, status
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from sqlalchemy.orm import (
    Session,
)

from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.helpers.handlers.friendship_handler import FriendshipHandler

from messenger.helpers.handlers.user_handler import UserHandler


def address_friendship_request(
    friendship_handler: FriendshipHandler,
    new_status_code_id: Literal[
        FriendshipStatusCode.ACCEPTED,
        FriendshipStatusCode.DECLINED,
    ],
) -> FriendshipStatusSchema:
    """Addresses a friendship request by either accepting or declining it.

    Args:
        friendship_service (FriendshipService): the friendship service that will
            be used to add the new status.
        new_status_code_id (Literal[FriendshipStatusCode.ACCEPTED, FriendshipStatusCode.DECLINED]):
            either accept or decline

    Raises:
        HTTPException: If the friendship was already addressed,
            or the friendship is blocked

    Returns:
        FriendshipStatusSchema: the new status that was created.
    """
    friendship_handler.raise_if_blocked()
    latest_status = friendship_handler.get_latest_friendship_status()

    if latest_status is not None and latest_status.status_code_id in (
        FriendshipStatusCode.ACCEPTED.value,
        FriendshipStatusCode.DECLINED.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="friend request already addressed",
        )

    return friendship_handler.add_new_status(
        friendship_handler.friendship.requester_id,
        friendship_handler.friendship.addressee_id,
        friendship_handler.friendship.addressee_id,
        new_status_code_id,
    )


def address_friendship_request_as_route(
    db: Session,
    current_user_id: int,
    requester_username: str,
    new_status_code_id: Literal[
        FriendshipStatusCode.ACCEPTED,
        FriendshipStatusCode.DECLINED,
    ],
):
    """Addresses a friendship by either accepting or declining it.

    Args:
        db (Session): the database session that will be used to add a new
            friendship status to the DB.
        current_user_id (int): the id of the current active user.
        requester_username (str): the username of the user that requested the
            friendship that the current_user will either accept or decline.
        new_status_code_id (Literal[ FriendshipStatusCode.ACCEPTED,
            FriendshipStatusCode.DECLINED, ]): either accept or decline
    """
    requester_handler = UserHandler(db)
    requester = requester_handler.get_user(
        UserSchema.username == requester_username
    )

    friendship_handler = FriendshipHandler(db)

    friendship_handler.get_friendship(
        current_user_id,
        requester.user_id,
    )

    address_friendship_request(
        friendship_handler,
        new_status_code_id,
    )
