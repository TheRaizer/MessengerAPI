from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from .conftest import current_active_user, usernames, session_mock


class TestSendFriendshipRequest:
    get_addressee = lambda self, username: UserSchema(
        user_id=1233,
        username=username,
        email="some-email",
        password_hash="some-hash",
    )

    @pytest.mark.parametrize("username", usernames)
    @patch("messenger.friends.router.FriendshipHandler")
    @patch("messenger.friends.router.UserHandler")
    def test_when_friendship_already_requested(
        self,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
        client: TestClient,
    ):
        addressee = self.get_addressee(username)
        UserHandlerMock.return_value.get_user.return_value = addressee

        friendship = FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=addressee.user_id,
            created_date_time=datetime.now(),
        )

        FriendshipHandlerMock.return_value.get_latest_friendship_status.return_value = (
            FriendshipStatusSchema(
                requester_id=current_active_user.user_id,
                addressee_id=addressee.user_id,
                specified_date_time=datetime.now(),
                status_code_id=FriendshipStatusCode.REQUESTED.value,
                specifier_id=current_active_user.user_id,
            )
        )

        FriendshipHandlerMock.return_value.get_friendship_bidirectional_query.return_value = (
            friendship
        )

        response = client.post(f"/friends/requests/send-request?username={username}")
        assert response.status_code == 400
        assert response.json() == {
            "detail": "you cannot send another friendship request",
        }

    @pytest.mark.parametrize("username", usernames)
    @patch("messenger.friends.router.FriendshipHandler")
    @patch("messenger.friends.router.UserHandler")
    def test_when_friendship_already_addressed(
        self,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
        client: TestClient,
    ):
        addressee = self.get_addressee(username)

        UserHandlerMock.return_value.get_user.return_value = addressee
        FriendshipHandlerMock.return_value.get_friendship_bidirectional_query.return_value = FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=addressee.user_id,
            created_date_time=datetime.now(),
        )

        response = client.post(f"/friends/requests/send-request?username={username}")
        assert response.status_code == 400
        assert response.json() == {"detail": "you cannot send a friendship request"}

    @freeze_time("2022-11-06")
    @pytest.mark.parametrize("username", usernames)
    @patch("messenger.friends.router.FriendshipHandler")
    @patch("messenger.friends.router.UserHandler")
    @patch("messenger.friends.router.FriendshipSchema")
    @patch("messenger.friends.router.FriendshipStatusSchema")
    def test_successfully_send_friendship_request(
        self,
        FriendshipStatusSchemaMock: MagicMock,
        FriendshipSchemaMock: MagicMock,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
        client: TestClient,
    ):
        addressee = self.get_addressee(username)
        UserHandlerMock.return_value.get_user.return_value = addressee
        FriendshipHandlerMock.return_value.get_friendship_bidirectional_query.return_value = (
            None
        )

        new_friendship_mock = FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=addressee.user_id,
            created_date_time=datetime.now(),
        )
        new_friendship_status_mock = FriendshipStatusSchema(
            requester_id=current_active_user.user_id,
            addressee_id=addressee.user_id,
            specified_date_time=datetime.now(),
            status_code_id=FriendshipStatusCode.REQUESTED.value,
            specifier_id=current_active_user.user_id,
        )
        FriendshipSchemaMock.return_value = new_friendship_mock
        FriendshipStatusSchemaMock.return_value = new_friendship_status_mock

        response = client.post(f"/friends/requests/send-request?username={username}")

        assert response.status_code == 201

        FriendshipSchemaMock.assert_called_once_with(
            requester_id=current_active_user.user_id,
            addressee_id=addressee.user_id,
            created_date_time=datetime.now(),
        )

        FriendshipStatusSchemaMock.assert_called_once_with(
            requester_id=current_active_user.user_id,
            addressee_id=addressee.user_id,
            specified_date_time=datetime.now(),
            status_code_id=FriendshipStatusCode.REQUESTED.value,
            specifier_id=current_active_user.user_id,
        )

        assert session_mock.add.call_count == 2

        session_mock.add.assert_any_call(FriendshipSchemaMock.return_value)
        session_mock.add.assert_any_call(FriendshipStatusSchemaMock.return_value)
        session_mock.commit.assert_called_once()

        assert response.json() == {
            "requester_id": new_friendship_mock.requester_id,
            "addressee_id": new_friendship_mock.addressee_id,
            "created_date_time": "2022-11-06T00:00:00",  # equivalent to the frozen time
        }
