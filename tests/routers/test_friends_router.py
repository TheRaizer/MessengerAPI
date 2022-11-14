from datetime import datetime
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema

app = FastAPI()
client = TestClient(app)


def test_get_friendships():
    with patch(
        "messenger.routers.friends.get_current_active_user"
    ) as get_current_active_user_mocks:
        test_user = UserSchema()
        friend_requests_sent = [
            FriendshipSchema(
                requester_id=1, addressee_id=2, created_date_time=datetime.now()
            )
        ]
        test_user.friend_requests_recieved = []
        test_user.friend_requests_sent = friend_requests_sent

        get_current_active_user_mocks.return_value = test_user
        response = client.get("/friends/")
        assert response.status_code == 200
        assert response.json() == {"recieved": [], "sent": friend_requests_sent}
