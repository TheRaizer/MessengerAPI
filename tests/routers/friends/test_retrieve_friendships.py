from datetime import datetime
from typing import Tuple
from fastapi.testclient import TestClient
from messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)


def test_get_friendship_requests_sent_produces_200(
    client: Tuple[TestClient, UserSchema]
):
    (test_client, _) = client

    response = test_client.get("/friends/requests/sent")
    assert response.status_code == 200


def test_get_friendship_requests_sent(client: Tuple[TestClient, UserSchema]):
    (test_client, current_active_user) = client

    expected_friendship_requests_sent = [
        FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=2,
            created_date_time=datetime.now(),
        ),
        FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=5,
            created_date_time=datetime.now(),
        ),
        FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=11,
            created_date_time=datetime.now(),
        ),
    ]

    current_active_user.friend_requests_sent = expected_friendship_requests_sent

    response = test_client.get("/friends/requests/sent")

    friendship_requests_sent = response.json()

    assert len(expected_friendship_requests_sent) == len(
        friendship_requests_sent
    )

    for friendship_request_sent, friendship_request_expected in zip(
        friendship_requests_sent, expected_friendship_requests_sent
    ):
        friendship = FriendshipSchema(**friendship_request_sent)
        assert friendship == friendship_request_expected


def test_get_friendship_requests_recieved_produces_200(
    client: Tuple[TestClient, UserSchema]
):
    (test_client, _) = client

    response = test_client.get("/friends/requests/recieved")
    assert response.status_code == 200


def test_get_friendship_requests_recieved(
    client: Tuple[TestClient, UserSchema]
):
    (test_client, current_active_user) = client

    expected_friendship_requests_recieved = [
        FriendshipSchema(
            requester_id=3,
            addressee_id=current_active_user.user_id,
            created_date_time=datetime.now(),
        ),
        FriendshipSchema(
            requester_id=8,
            addressee_id=current_active_user.user_id,
            created_date_time=datetime.now(),
        ),
        FriendshipSchema(
            requester_id=896,
            addressee_id=current_active_user.user_id,
            created_date_time=datetime.now(),
        ),
    ]

    current_active_user.friend_requests_recieved = (
        expected_friendship_requests_recieved
    )

    response = test_client.get("/friends/requests/recieved")

    friendship_requests_recieved = response.json()

    assert len(friendship_requests_recieved) == len(
        expected_friendship_requests_recieved
    )

    for friendship_request_recieved, friendship_request_expected in zip(
        friendship_requests_recieved, expected_friendship_requests_recieved
    ):
        friendship = FriendshipSchema(**friendship_request_recieved)
        assert friendship == friendship_request_expected
