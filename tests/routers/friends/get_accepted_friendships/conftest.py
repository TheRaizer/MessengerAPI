from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy.orm import Session

from messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.constants.pagination import CursorState

from messenger.models.fastapi.user_model import UserModel
from tests.conftest import generate_username, get_user_schema_params

get_first_page_params = (
    "friend_data, accepted_friend_ids, limit, expected_next_cursor",
    [
        (
            [
                (2, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.BLOCKED),
                (42, FriendshipStatusCode.ACCEPTED),
            ],
            [42],
            "4",
            None,
        ),
        (
            [
                (3, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
                (7, FriendshipStatusCode.ACCEPTED),
            ],
            [3, 4, 5],
            "3",
            CursorState.NEXT.value + "___" + generate_username(5),
        ),
        (
            [
                (902, FriendshipStatusCode.BLOCKED),
                (32, FriendshipStatusCode.REQUESTED),
                (9, FriendshipStatusCode.ACCEPTED),
                (9, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.REQUESTED),
            ],
            [],
            "2",
            None,
        ),
    ],
)

get_middle_page_params = (
    "friend_data, accepted_friend_ids, limit, cursor, expected_next_cursor, expected_previous_cursor",
    [
        (
            [
                (2, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.BLOCKED),
                (7, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
                (8, FriendshipStatusCode.ACCEPTED),
            ],
            [6, 7],
            "2",
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.NEXT.value + "___" + generate_username(7),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
        ),
        (
            [
                (3, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
                (7, FriendshipStatusCode.ACCEPTED),
            ],
            [4],
            "1",
            CursorState.PREVIOUS.value + "___" + generate_username(5),
            CursorState.NEXT.value + "___" + generate_username(4),
            CursorState.PREVIOUS.value + "___" + generate_username(4),
        ),
        (
            [
                (902, FriendshipStatusCode.BLOCKED),
                (32, FriendshipStatusCode.REQUESTED),
                (9, FriendshipStatusCode.ACCEPTED),
                (9, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.REQUESTED),
                (3, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
            ],
            [4, 5],
            "2",
            CursorState.PREVIOUS.value + "___" + generate_username(6),
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.PREVIOUS.value + "___" + generate_username(4),
        ),
    ],
)

get_last_page_params = (
    "friend_data, accepted_friend_ids, limit, cursor, expected_previous_cursor",
    [
        (
            [
                (2, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.BLOCKED),
                (7, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
                (8, FriendshipStatusCode.ACCEPTED),
            ],
            [6, 7, 8],
            "3",
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
        ),
        (
            [
                (3, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
                (7, FriendshipStatusCode.ACCEPTED),
            ],
            [6, 7],
            "5",
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
        ),
        (
            [
                (902, FriendshipStatusCode.BLOCKED),
                (32, FriendshipStatusCode.REQUESTED),
                (9, FriendshipStatusCode.ACCEPTED),
                (9, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.REQUESTED),
                (3, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.ACCEPTED),
                (5, FriendshipStatusCode.ACCEPTED),
                (6, FriendshipStatusCode.ACCEPTED),
            ],
            [4, 5, 6],
            "3",
            CursorState.NEXT.value + "___" + generate_username(3),
            CursorState.PREVIOUS.value + "___" + generate_username(4),
        ),
    ],
)


valid_query_params = [
    ("5", CursorState.NEXT.value + "___2"),
    ("3", CursorState.PREVIOUS.value + "___4"),
    ("23", CursorState.NEXT.value + "___username-email23"),
    ("1", None),
]


def add_friendships(
    friend_data: List[Tuple[int, FriendshipStatusCode]],
    accepted_friend_ids: List[int],
    current_active_user_id: int,
    session: Session,
):
    # keep track of users created so we don't attempt to create
    # multiple users with the same id.
    users_created: List[int] = []

    # the users we expect to recieve as output from the route.
    expected_users: List[UserModel] = []

    for i, (id, status) in enumerate(friend_data):
        if id not in users_created:
            users_created.append(id)
            friend_user = UserSchema(**get_user_schema_params(id))

            if id in accepted_friend_ids:
                expected_users.append(UserModel.from_orm(friend_user))

            friendship = FriendshipSchema(
                requester_id=current_active_user_id,
                addressee_id=id,
                created_date_time=datetime.now() + timedelta(hours=i),
            )
            session.add(friendship)
            session.add(friend_user)

        friendship_status = FriendshipStatusSchema(
            requester_id=current_active_user_id,
            addressee_id=id,
            specified_date_time=datetime.now() + timedelta(hours=i),
            status_code_id=status.value,
            specifier_id=id,
        )

        session.add(friendship_status)

    session.commit()

    return expected_users
