from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.conftest import add_initial_friendship_status_codes


def initialize_friendship_request_addressed_to_current_user(
    session: Session,
    current_active_user: UserSchema,
    username: str,
    email: str,
    password: str,
    initial_friendship_status_code: Optional[FriendshipStatusCode] = None,
):
    add_initial_friendship_status_codes(session)
    friendship_status_code = (
        FriendshipStatusCode.REQUESTED
        if initial_friendship_status_code is None
        else initial_friendship_status_code
    )
    friendship_requester = UserSchema(
        user_id=current_active_user.user_id + 1,
        username=username,
        password_hash=password,
        email=email,
    )
    friendship = FriendshipSchema(
        requester_id=friendship_requester.user_id,
        addressee_id=current_active_user.user_id,
        created_date_time=datetime.now() - timedelta(minutes=13),
    )
    friendship_status = FriendshipStatusSchema(
        requester_id=friendship.requester_id,
        addressee_id=friendship.addressee_id,
        status_code_id=friendship_status_code.value,
        specified_date_time=datetime.now() - timedelta(minutes=13),
        specifier_id=friendship_requester.user_id,
    )

    session.add(friendship_requester)
    session.add(friendship)
    session.add(friendship_status)

    session.commit()

    return (friendship, friendship_requester)
