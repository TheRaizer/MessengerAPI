from fastapi.testclient import TestClient
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from .conftest import (
    friendship_requests_recieved,
    friendship_requests_sent,
)


def test_get_friendship_requests_sent(client: TestClient):
    response = client.get("/friends/requests/sent")
    assert response.status_code == 200

    arr = response.json()

    assert len(friendship_requests_sent) == len(arr)

    for res_friendship_dict, friendship_expected in zip(arr, friendship_requests_sent):
        friendship = FriendshipSchema(**res_friendship_dict)
        assert friendship == friendship_expected


def test_get_friendship_requests_recieved(client: TestClient):
    response = client.get("/friends/requests/recieved")
    assert response.status_code == 200

    arr = response.json()

    assert len(friendship_requests_recieved) == len(arr)

    for res_friendship_dict, friendship_expected in zip(
        arr, friendship_requests_recieved
    ):
        friendship = FriendshipSchema(**res_friendship_dict)
        assert friendship == friendship_expected
