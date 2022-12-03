from typing import Literal
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.friends.friendship_handler import (
    FriendshipHandler,
    address_friendship_request,
)
from sqlalchemy.orm import Session

from messenger.helpers.user_handler import UserHandler


def address_friendship_request_as_route(
    db: Session,
    current_user: UserSchema,
    requester_username: str,
    new_status_code_id: Literal[
        FriendshipStatusCode.ACCEPTED, FriendshipStatusCode.DECLINED
    ],
):
    addressee_handler = UserHandler(db)
    addressee = addressee_handler.get_user(UserSchema.username == requester_username)

    friendship_handler = FriendshipHandler(db)

    friendship_handler.get_friendship_bidirectional_query(addressee, current_user)

    address_friendship_request(friendship_handler, new_status_code_id)
