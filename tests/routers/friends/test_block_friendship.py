from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from freezegun import freeze_time
from requests import Response
from fastapi.testclient import TestClient
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.routers.friends.conftest import current_active_user
from tests.conftest import valid_usernames


class TestBlockFriendship:
    get_user_to_block = lambda self, username: UserSchema(
        user_id=1224, username={username}, password_hash="some_hash"
    )

    def on_success_assertions(
        self,
        response: Response,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        user_to_block: UserSchema,
    ):
        assert response.status_code == 201
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

    @pytest.mark.parametrize("username", valid_usernames)
    @patch("messenger.routers.friends.FriendshipHandler")
    @patch("messenger.routers.friends.UserHandler")
    def test_when_friendship_exists(
        self,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
        client: TestClient,
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
        self.on_success_assertions(
            response, UserHandlerMock, FriendshipHandlerMock, user_to_block
        )

    @freeze_time("2022-11-06")
    @pytest.mark.parametrize("username", valid_usernames)
    @patch("messenger.routers.friends.FriendshipHandler")
    @patch("messenger.routers.friends.UserHandler")
    def test_when_friendship_does_not_exist(
        self,
        UserHandlerMock: MagicMock,
        FriendshipHandlerMock: MagicMock,
        username: str,
        client: TestClient,
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

        response: Response

        with patch(
            "messenger.routers.friends.FriendshipSchema"
        ) as FriendshipSchemaMock:
            FriendshipSchemaMock.return_value = friendship_to_create
            response = client.post(
                f"friends/requests/block?user_to_block_username={username}"
            )
            FriendshipSchemaMock.assert_called_once_with(
                requester_id=friendship_to_create.requester_id,
                addressee_id=friendship_to_create.addressee_id,
                created_date_time=friendship_to_create.created_date_time,
            )
            assert (
                FriendshipHandlerMock.return_value.friendship
                == friendship_to_create
            )
            session_mock.add.assert_called_once_with(
                FriendshipSchemaMock.return_value
            )

        self.on_success_assertions(
            response, UserHandlerMock, FriendshipHandlerMock, user_to_block
        )
