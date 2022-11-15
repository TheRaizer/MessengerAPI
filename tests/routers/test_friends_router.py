from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.fastApi import app
from fastapi.testclient import TestClient
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
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


async def override_get_current_active_user():
    current_active_user.friend_requests_recieved = friendship_requests_recieved
    current_active_user.friend_requests_sent = friendship_requests_sent

    yield current_active_user


session_mock = MagicMock()


async def override_database_session():
    yield session_mock
    session_mock.reset_mock()


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
def test_accept_friendship_request(username: str):
    with patch(
        "messenger.routers.friends.address_friendship_request_as_route"
    ) as address_friendship_request_as_route_mock:
        response = client.post(
            f"/friends/requests/accept?requester_username={username}"
        )

        assert response.status_code == 201
        address_friendship_request_as_route_mock.assert_called_once_with(
            session_mock,
            current_active_user,
            username,
            FriendshipStatusCode.ACCEPTED,
        )


@pytest.mark.parametrize("username", ["ome_2name12", "pillsubryw22", "testtest_"])
def test_decline_friendship_request(username):
    with patch(
        "messenger.routers.friends.address_friendship_request_as_route"
    ) as address_friendship_request_as_route_mock:
        response = client.post(
            f"/friends/requests/decline?requester_username={username}"
        )

        assert response.status_code == 201
        address_friendship_request_as_route_mock.assert_called_once_with(
            session_mock,
            current_active_user,
            username,
            FriendshipStatusCode.DECLINED,
        )
