from datetime import datetime, timedelta
from typing import List, Tuple
from fastapi.testclient import TestClient
from freezegun import freeze_time
import pytest
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.conftest import add_initial_friendship_status_codes
from tests.routers.friends.conftest import FROZEN_DATE


@freeze_time(FROZEN_DATE)
class TestGetAcceptedFriendships:
    def test_produces_200_when_successful(
        self, client: Tuple[TestClient, UserSchema]
    ):
        (test_client, _) = client

        response = test_client.get("/friends/requests/accepted")
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "friend_data, expected_output",
        [
            (
                [
                    (2, FriendshipStatusCode.ACCEPTED),
                    (4, FriendshipStatusCode.REQUESTED),
                    (2, FriendshipStatusCode.BLOCKED),
                    (42, FriendshipStatusCode.ACCEPTED),
                ],
                [42],
            ),
            (
                [
                    (22, FriendshipStatusCode.ACCEPTED),
                    (5, FriendshipStatusCode.ACCEPTED),
                    (2, FriendshipStatusCode.DECLINED),
                    (3, FriendshipStatusCode.ACCEPTED),
                ],
                [22, 5, 3],
            ),
            (
                [
                    (902, FriendshipStatusCode.BLOCKED),
                    (32, FriendshipStatusCode.REQUESTED),
                    (9, FriendshipStatusCode.ACCEPTED),
                    (9, FriendshipStatusCode.BLOCKED),
                    (3, FriendshipStatusCode.REQUESTED),
                    (2, FriendshipStatusCode.DECLINED),
                    (6, FriendshipStatusCode.REQUESTED),
                ],
                [],
            ),
        ],
    )
    def test_retrieves_list_of_accepted_friendships(
        self,
        friend_data: List[Tuple[int, FriendshipStatusCode]],
        expected_output: List[int],
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        users_created: List[int] = []

        for i, (id, status) in enumerate(friend_data):
            if id not in users_created:
                users_created.append(id)
                friend_user = UserSchema(
                    user_id=id,
                    username="username" + str(i),
                    email="email" + str(i),
                    password_hash="password",
                )
                friendship = FriendshipSchema(
                    requester_id=current_active_user.user_id,
                    addressee_id=id,
                    created_date_time=datetime.now() + timedelta(hours=i),
                )
                session.add(friendship)
                session.add(friend_user)

            friendship_status = FriendshipStatusSchema(
                requester_id=current_active_user.user_id,
                addressee_id=id,
                specified_date_time=datetime.now() + timedelta(hours=i),
                status_code_id=status.value,
                specifier_id=id,
            )

            session.add(friendship_status)

        session.commit()

        response = test_client.get("/friends/requests/accepted")

        assert response.json().sort() == expected_output.sort()