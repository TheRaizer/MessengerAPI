from typing import List, Tuple
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from tests.conftest import (
    add_initial_friendship_status_codes,
    generate_username,
)
from tests.routers.friends.conftest import add_friendships
from tests.routers.friends.cancel_friend_request.conftest import (
    produce_400_data,
    cancellable_friend_request_data,
)


class TestCancelFriendshipRequest:
    def test_produces_201_when_successful(
        self,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client

        add_initial_friendship_status_codes(session)

        add_friendships(
            [(2, FriendshipStatusCode.REQUESTED)],
            [2],
            current_active_user.user_id,
            session,
        )

        response = test_client.post(
            f"/friends/requests/cancel?request_addressee_username={generate_username(2)}"
        )
        assert response.status_code == 201

    def test_produces_404_when_friendship_does_not_exist(
        self,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, _) = client

        response = test_client.post(
            f"/friends/requests/cancel?request_addressee_username={generate_username(2)}"
        )
        assert response.status_code == 404

    @pytest.mark.parametrize(produce_400_data[0], produce_400_data[1])
    def test_produces_400_when_friendship_does_not_have_requested_latest_status(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        addressee_user_id: int,
        addressee_username: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client

        add_initial_friendship_status_codes(session)

        add_friendships(
            friend_data,
            [addressee_user_id],
            current_active_user.user_id,
            session,
        )

        response = test_client.post(
            f"/friends/requests/cancel?request_addressee_username={addressee_username}"
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        cancellable_friend_request_data[0], cancellable_friend_request_data[1]
    )
    def test_successfully_cancels_friend_request(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        addressee_user_id: int,
        addressee_username: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client

        add_initial_friendship_status_codes(session)

        add_friendships(
            friend_data,
            [addressee_user_id],
            current_active_user.user_id,
            session,
        )

        response = test_client.post(
            f"/friends/requests/cancel?request_addressee_username={addressee_username}"
        )

        assert response.status_code == 201

        # friendship and its statuses should be removed from the database
        friendship = (
            session.query(FriendshipSchema)
            .filter(
                FriendshipSchema.addressee_id == addressee_user_id,
                FriendshipSchema.requester_id == current_active_user.user_id,
            )
            .first()
        )

        friendship_statuses = (
            session.query(FriendshipStatusSchema)
            .filter(
                FriendshipStatusSchema.addressee_id == addressee_user_id,
                FriendshipStatusSchema.requester_id
                == current_active_user.user_id,
            )
            .all()
        )

        assert friendship is None
        assert len(friendship_statuses) == 0
