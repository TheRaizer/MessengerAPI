from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.conftest import generate_username


produce_400_data = (
    "friend_data, addressee_user_id, addressee_username",
    [
        (
            [
                (2, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.REQUESTED),
                (2, FriendshipStatusCode.BLOCKED),
                (42, FriendshipStatusCode.ACCEPTED),
                (4, FriendshipStatusCode.BLOCKED),
            ],
            [4],
            generate_username(4),
        ),
        (
            [
                (3, FriendshipStatusCode.BLOCKED),
                (5, FriendshipStatusCode.BLOCKED),
                (2, FriendshipStatusCode.DECLINED),
                (4, FriendshipStatusCode.BLOCKED),
                (6, FriendshipStatusCode.BLOCKED),
                (7, FriendshipStatusCode.BLOCKED),
            ],
            [2],
            generate_username(2),
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
            [32],
            generate_username(32),
        ),
    ],
)
