from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from .conftest import current_active_user, usernames, session_mock


@pytest.mark.parametrize("username", usernames)
@patch("messenger.routers.friends.address_friendship_request_as_route")
def test_accept_friendship_request(
    address_friendship_request_as_route_mock: MagicMock,
    username: str,
    client: TestClient,
):
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


@pytest.mark.parametrize("username", usernames)
@patch("messenger.routers.friends.address_friendship_request_as_route")
def test_decline_friendship_request(
    address_friendship_request_as_route_mock: MagicMock,
    username: str,
    client: TestClient,
):
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
