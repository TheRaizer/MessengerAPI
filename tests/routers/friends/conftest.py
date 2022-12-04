from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from _submodules.messenger_utils.messenger_schemas.schema import (
    database_session,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.fastApi import app
from messenger.helpers.users import get_current_active_user


friendship_requests_sent = [
    FriendshipSchema(
        requester_id=1, addressee_id=2, created_date_time=datetime.now()
    ),
    FriendshipSchema(
        requester_id=1, addressee_id=5, created_date_time=datetime.now()
    ),
    FriendshipSchema(
        requester_id=1, addressee_id=11, created_date_time=datetime.now()
    ),
]
friendship_requests_recieved = [
    FriendshipSchema(
        requester_id=3, addressee_id=1, created_date_time=datetime.now()
    ),
    FriendshipSchema(
        requester_id=8, addressee_id=1, created_date_time=datetime.now()
    ),
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


session_mock = MagicMock()


def override_database_session():
    session_mock.reset_mock()
    return session_mock


def override_get_current_active_user():
    current_active_user.friend_requests_recieved = friendship_requests_recieved
    current_active_user.friend_requests_sent = friendship_requests_sent

    return current_active_user


@pytest.fixture
def client():
    app.dependency_overrides[
        get_current_active_user
    ] = override_get_current_active_user
    app.dependency_overrides[database_session] = override_database_session

    test_client = TestClient(app)

    return test_client


usernames = ["helloooo_wORLd23", "3322_Wad", "_puT_223D"]
