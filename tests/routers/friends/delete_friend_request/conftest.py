from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.conftest import generate_username


friend_request_data = (
    "friend_data, addressee_user_id, addressee_username",
    [
        (
            [
                (2, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.BLOCKED),
                (42, FriendshipStatusCode.REQUESTED),
                (4, FriendshipStatusCode.BLOCKED),
            ],
            42,
            generate_username(42),
        ),
        (
            [
                (3, FriendshipStatusCode.BLOCKED),
                (5, FriendshipStatusCode.BLOCKED),
                (7, FriendshipStatusCode.REQUESTED),
            ],
            7,
            generate_username(7),
        ),
        (
            [
                (2, FriendshipStatusCode.BLOCKED),
                (9, FriendshipStatusCode.ACCEPTED),
                (3, FriendshipStatusCode.DECLINED),
                (6, FriendshipStatusCode.REQUESTED),
            ],
            6,
            generate_username(6),
        ),
    ],
)
