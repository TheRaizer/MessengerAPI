from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.constants.pagination import CursorState
from tests.conftest import generate_username

get_first_page_params = (
    "friend_data, friend_requester_ids, limit, expected_next_cursor",
    [
        (
            [
                (2, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.BLOCKED),
                (42, FriendshipStatusCode.ACCEPTED),
            ],
            [4],
            "4",
            None,
        ),
        (
            [
                (3, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
                (7, FriendshipStatusCode.REQUESTED),
            ],
            [3, 4, 5],
            "3",
            CursorState.NEXT.value + "___" + generate_username(5),
        ),
        (
            [
                (902, FriendshipStatusCode.BLOCKED),
                (32, FriendshipStatusCode.ACCEPTED),
                (9, FriendshipStatusCode.ACCEPTED),
                (9, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.ACCEPTED),
                (2, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.ACCEPTED),
            ],
            [],
            "2",
            None,
        ),
    ],
)

get_middle_page_params = (
    "friend_data, friend_requester_ids, limit, cursor, expected_next_cursor, expected_previous_cursor",
    [
        (
            [
                (2, FriendshipStatusCode.REQUESTED),
                (4, FriendshipStatusCode.ACCEPTED),
                (2, FriendshipStatusCode.BLOCKED),
                (7, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
                (8, FriendshipStatusCode.REQUESTED),
            ],
            [6, 7],
            "2",
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.NEXT.value + "___" + generate_username(7),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
        ),
        (
            [
                (3, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
                (7, FriendshipStatusCode.REQUESTED),
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
                (32, FriendshipStatusCode.BLOCKED),
                (9, FriendshipStatusCode.REQUESTED),
                (9, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.DECLINED),
                (2, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.REQUESTED),
                (4, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
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
    "friend_data, friend_requester_ids, limit, cursor, expected_previous_cursor",
    [
        (
            [
                (2, FriendshipStatusCode.REQUESTED),
                (4, FriendshipStatusCode.DECLINED),
                (2, FriendshipStatusCode.BLOCKED),
                (7, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
                (8, FriendshipStatusCode.REQUESTED),
            ],
            [6, 7, 8],
            "3",
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
        ),
        (
            [
                (3, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
                (7, FriendshipStatusCode.REQUESTED),
            ],
            [6, 7],
            "5",
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
        ),
        (
            [
                (902, FriendshipStatusCode.BLOCKED),
                (32, FriendshipStatusCode.BLOCKED),
                (9, FriendshipStatusCode.REQUESTED),
                (9, FriendshipStatusCode.BLOCKED),
                (3, FriendshipStatusCode.DECLINED),
                (2, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.ACCEPTED),
                (3, FriendshipStatusCode.REQUESTED),
                (4, FriendshipStatusCode.REQUESTED),
                (5, FriendshipStatusCode.REQUESTED),
                (6, FriendshipStatusCode.REQUESTED),
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
    ("23", CursorState.NEXT.value + "___23"),
    ("1", None),
]
