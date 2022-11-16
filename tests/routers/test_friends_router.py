from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time

from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.fastApi import app
from messenger.helpers.users import get_current_active_user

friendship_requests_sent = [
    FriendshipSchema(requester_id=1, addressee_id=2, created_date_time=datetime.now()),
    FriendshipSchema(requester_id=1, addressee_id=5, created_date_time=datetime.now()),
    FriendshipSchema(requester_id=1, addressee_id=11, created_date_time=datetime.now()),
]
friendship_requests_recieved = [
    FriendshipSchema(requester_id=3, addressee_id=1, created_date_time=datetime.now()),
    FriendshipSchema(requester_id=8, addressee_id=1, created_date_time=datetime.now()),
    FriendshipSchema(
        requester_id=896, addressee_id=1, created_date_time=datetime.now()
    ),
]

current_active_user = UserSchema(
    user_id=1,
    username="test-username",
    email="test-email",
    password_hash="test-password-hash",
)


def override_get_current_active_user():
    current_active_user.friend_requests_recieved = friendship_requests_recieved
    current_active_user.friend_requests_sent = friendship_requests_sent

    return current_active_user


session_mock = MagicMock()


def override_database_session():
    session_mock.reset_mock()
    return session_mock


client = TestClient(app)
app.dependency_overrides[get_current_active_user] = override_get_current_active_user
app.dependency_overrides[database_session] = override_database_session


def test_get_friendship_requests_sent():
    response = client.get("/friends/requests/sent")
    assert response.status_code == 200

    arr = response.json()

    assert len(friendship_requests_sent) == len(arr)

    for res_friendship_dict, friendship_expected in zip(arr, friendship_requests_sent):
        friendship = FriendshipSchema(**res_friendship_dict)
        assert friendship == friendship_expected


def test_get_friendship_requests_recieved():
    response = client.get("/friends/requests/recieved")
    assert response.status_code == 200

    arr = response.json()

    assert len(friendship_requests_recieved) == len(arr)

    for res_friendship_dict, friendship_expected in zip(
        arr, friendship_requests_recieved
    ):
        friendship = FriendshipSchema(**res_friendship_dict)
        assert friendship == friendship_expected


@pytest.mark.parametrize("username", ["Some_username12", "_another_user", "hi_im_user"])
@patch("messenger.routers.friends.address_friendship_request_as_route")
def test_accept_friendship_request(
    address_friendship_request_as_route_mock: MagicMock, username: str
):
    response = client.post(f"/friends/requests/accept?requester_username={username}")

    assert response.status_code == 201
    address_friendship_request_as_route_mock.assert_called_once_with(
        session_mock,
        current_active_user,
        username,
        FriendshipStatusCode.ACCEPTED,
    )


@pytest.mark.parametrize("username", ["ome_2name12", "pillsubryw22", "testtest_"])
@patch("messenger.routers.friends.address_friendship_request_as_route")
def test_decline_friendship_request(
    address_friendship_request_as_route_mock: MagicMock, username: str
):
    response = client.post(f"/friends/requests/decline?requester_username={username}")

    assert response.status_code == 201
    address_friendship_request_as_route_mock.assert_called_once_with(
        session_mock,
        current_active_user,
        username,
        FriendshipStatusCode.DECLINED,
    )


class TestBlockFriendship:
    get_user_to_block = lambda self, username: UserSchema(
        user_id=1224, username={username}, password_hash="some_hash"
    )

    @pytest.mark.parametrize("username", ["helloooo_wORLd23", "3322_Wad", "_puT_223D"])
    @patch("messenger.routers.friends.FriendshipHandler")
    @patch("messenger.routers.friends.UserHandler")
    def test_when_friendship_exists(
        self,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
    ):
        user_to_block = self.get_user_to_block(username)
        friendship_to_block = FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=user_to_block.user_id,
            created_date_time=datetime.now(),
        )

        UserHandlerMock.return_value.get_user.return_value = user_to_block
        FriendshipHandlerMock.get_friendship_bidirectional_query.return_value = (
            friendship_to_block
        )

        response = client.post(
            f"friends/requests/block?user_to_block_username={username}"
        )

        UserHandlerMock.assert_called_once()
        assert response.status_code == 201
        UserHandlerMock.return_value.get_user.assert_called_once()
        FriendshipHandlerMock.return_value.get_friendship_bidirectional_query.assert_called_once_with(
            user_to_block, current_active_user
        )
        FriendshipHandlerMock.return_value.add_new_status.assert_called_once_with(
            FriendshipHandlerMock().friendship.requester_id,
            FriendshipHandlerMock().friendship.addressee_id,
            current_active_user.user_id,
            FriendshipStatusCode.BLOCKED,
        )

    @freeze_time("2022-11-06")
    @pytest.mark.parametrize("username", ["helloooo_wORLd23", "3322_Wad", "_puT_223D"])
    @patch("messenger.routers.friends.FriendshipHandler")
    @patch("messenger.routers.friends.UserHandler")
    def test_when_friendship_does_not_exist(
        self,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
    ):
        user_to_block = self.get_user_to_block(username)
        friendship_to_create = FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=user_to_block.user_id,
            created_date_time=datetime.now(),
        )

        UserHandlerMock.return_value.get_user.return_value = user_to_block
        FriendshipHandlerMock.return_value.get_friendship_bidirectional_query.return_value = (
            None
        )

        with patch(
            "messenger.routers.friends.FriendshipSchema"
        ) as FriendshipSchemaMock:
            FriendshipSchemaMock.return_value = friendship_to_create
            response = client.post(
                f"friends/requests/block?user_to_block_username={username}"
            )
            assert response.status_code == 201
            FriendshipSchemaMock.assert_called_once_with(
                requester_id=friendship_to_create.requester_id,
                addressee_id=friendship_to_create.addressee_id,
                created_date_time=friendship_to_create.created_date_time,
            )
            assert FriendshipHandlerMock.return_value.friendship == friendship_to_create
            session_mock.add.assert_called_once_with(FriendshipSchemaMock.return_value)

        UserHandlerMock.assert_called_once()
        UserHandlerMock.return_value.get_user.assert_called_once()
        FriendshipHandlerMock.return_value.get_friendship_bidirectional_query.assert_called_once_with(
            user_to_block, current_active_user
        )
        FriendshipHandlerMock.return_value.add_new_status.assert_called_once_with(
            FriendshipHandlerMock().friendship.requester_id,
            FriendshipHandlerMock().friendship.addressee_id,
            current_active_user.user_id,
            FriendshipStatusCode.BLOCKED,
        )
