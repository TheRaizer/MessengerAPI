from typing import List, Optional, Tuple
from fastapi.testclient import TestClient
from freezegun import freeze_time
import pytest
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.conftest import add_initial_friendship_status_codes
from tests.routers.friends.conftest import FROZEN_DATE, add_friendships
from tests.routers.friends.get_friend_request_senders.conftest import (
    get_first_page_params,
    get_middle_page_params,
    get_last_page_params,
    valid_query_params,
)
from tests.helpers.dependencies.pagination.conftest import invalid_cursors


@freeze_time(FROZEN_DATE)
class TestGetFriendRequestSenders:
    @pytest.mark.parametrize("limit, cursor", valid_query_params)
    def test_produces_200_when_successful(
        self,
        limit: str,
        cursor: Optional[str],
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, _) = client

        cursor = "" if cursor is None else f"cursor={cursor}"
        response = test_client.get(
            f"/friends/requests/senders?limit={limit}&{cursor}"
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("invalid_cursor", invalid_cursors)
    def test_produces_400_when_cursor_invalid(
        self, invalid_cursor: str, client: Tuple[TestClient, UserSchema]
    ):
        (test_client, _) = client

        response = test_client.get(
            f"/friends/requests/senders?limit=2&cursor={invalid_cursor}"
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "invalid cursor"}

    @pytest.mark.parametrize(get_first_page_params[0], get_first_page_params[1])
    def test_retrieves_first_page(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        friend_requester_ids: List[int],
        limit: str,
        expected_next_cursor: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        expected_users = add_friendships(
            friend_data,
            friend_requester_ids,
            current_active_user.user_id,
            session,
            active_user_is_requester=False,
        )

        response = test_client.get(f"/friends/requests/senders?limit={limit}")

        assert len(response.json()["results"]) == len(expected_users)
        assert sorted(
            response.json()["results"],
            key=lambda user_model: user_model["user_id"],
        ) == sorted(expected_users, key=lambda user_model: user_model.user_id)

    @pytest.mark.parametrize(get_first_page_params[0], get_first_page_params[1])
    def test_retrieves_correct_cursor_when_first_page(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        friend_requester_ids: List[int],
        limit: str,
        expected_next_cursor: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        add_friendships(
            friend_data,
            friend_requester_ids,
            current_active_user.user_id,
            session,
            active_user_is_requester=False,
        )

        response = test_client.get(f"/friends/requests/senders?limit={limit}")

        cursor = response.json()["cursor"]

        assert cursor["next_page"] == expected_next_cursor
        assert cursor["prev_page"] is None

    @pytest.mark.parametrize(
        get_middle_page_params[0], get_middle_page_params[1]
    )
    def test_retrieves_middle_page(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        friend_requester_ids: List[int],
        limit: str,
        cursor: str,
        expected_next_cursor: str,
        expected_previous_cursor: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        expected_users = add_friendships(
            friend_data,
            friend_requester_ids,
            current_active_user.user_id,
            session,
            active_user_is_requester=False,
        )

        response = test_client.get(
            f"/friends/requests/senders?limit={limit}&cursor={cursor}"
        )

        assert len(response.json()["results"]) == len(expected_users)

        assert sorted(
            response.json()["results"],
            key=lambda user_model: user_model["user_id"],
        ) == sorted(expected_users, key=lambda user_model: user_model.user_id)

    @pytest.mark.parametrize(
        get_middle_page_params[0], get_middle_page_params[1]
    )
    def test_retrieves_correct_cursor_when_middle_page(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        friend_requester_ids: List[int],
        limit: str,
        cursor: str,
        expected_next_cursor: str,
        expected_previous_cursor: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        add_friendships(
            friend_data,
            friend_requester_ids,
            current_active_user.user_id,
            session,
            active_user_is_requester=False,
        )

        response = test_client.get(
            f"/friends/requests/senders?limit={limit}&cursor={cursor}"
        )

        response_cursor = response.json()["cursor"]

        assert response_cursor["next_page"] == expected_next_cursor
        assert response_cursor["prev_page"] == expected_previous_cursor

    @pytest.mark.parametrize(get_last_page_params[0], get_last_page_params[1])
    def test_retrieves_last_page(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        friend_requester_ids: List[int],
        limit: str,
        cursor: str,
        expected_previous_cursor: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        expected_users = add_friendships(
            friend_data,
            friend_requester_ids,
            current_active_user.user_id,
            session,
            active_user_is_requester=False,
        )

        response = test_client.get(
            f"/friends/requests/senders?limit={limit}&cursor={cursor}"
        )

        assert len(response.json()["results"]) == len(expected_users)
        assert sorted(
            response.json()["results"],
            key=lambda user_model: user_model["user_id"],
        ) == sorted(expected_users, key=lambda user_model: user_model.user_id)

    @pytest.mark.parametrize(get_last_page_params[0], get_last_page_params[1])
    def test_retrieves_correct_cursor_when_last_page(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        friend_requester_ids: List[int],
        limit: str,
        cursor: str,
        expected_previous_cursor: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        add_friendships(
            friend_data,
            friend_requester_ids,
            current_active_user.user_id,
            session,
            active_user_is_requester=False,
        )

        response = test_client.get(
            f"/friends/requests/senders?limit={limit}&cursor={cursor}"
        )

        response_cursor = response.json()["cursor"]

        assert response_cursor["next_page"] is None
        assert response_cursor["prev_page"] == expected_previous_cursor
