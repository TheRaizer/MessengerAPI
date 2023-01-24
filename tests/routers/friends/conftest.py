from datetime import datetime, timedelta
from typing import List, Tuple
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from messenger_schemas.schema import (
    database_session,
)
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
from messenger.fastApi import app
from messenger.helpers.dependencies.user import get_current_active_user
from messenger.models.fastapi.user_model import UserModel
from tests.conftest import get_user_schema_params


@pytest.fixture
def client(session: Session):
    current_active_user = UserSchema(
        user_id=1,
        username="test-username",
        email="test-email",
        password_hash="test-password-hash",
    )

    session.add(current_active_user)
    session.commit()
    session.refresh(current_active_user)

    def override_database_session():
        yield session

    def override_get_current_active_user():
        yield current_active_user

    app.dependency_overrides[
        get_current_active_user
    ] = override_get_current_active_user
    app.dependency_overrides[database_session] = override_database_session

    test_client = TestClient(app)

    yield (test_client, current_active_user)

    del app.dependency_overrides[database_session]
    del app.dependency_overrides[get_current_active_user]


FROZEN_DATE = "2022-11-07"


def add_friendships(
    friend_data: List[Tuple[int, FriendshipStatusCode]],
    friend_ids: List[int],
    current_active_user_id: int,
    session: Session,
    active_user_is_requester: bool = True,
):
    # keep track of users created so we don't attempt to create
    # multiple users with the same id.
    users_created: List[int] = []

    # the users we expect to recieve as output from the route.
    expected_users: List[UserModel] = []

    for i, (friend_id, status) in enumerate(friend_data):
        requester_id = (
            current_active_user_id if active_user_is_requester else friend_id
        )
        addressee_id = (
            friend_id if active_user_is_requester else current_active_user_id
        )

        if friend_id not in users_created:
            users_created.append(friend_id)
            friend_user = UserSchema(**get_user_schema_params(friend_id))
            friendship = FriendshipSchema(
                requester_id=requester_id,
                addressee_id=addressee_id,
                created_date_time=datetime.now() + timedelta(hours=i),
            )

            if friend_id in friend_ids:
                expected_users.append(UserModel.from_orm(friend_user))

            session.add(friendship)
            session.add(friend_user)

        friendship_status = FriendshipStatusSchema(
            requester_id=requester_id,
            addressee_id=addressee_id,
            specified_date_time=datetime.now() + timedelta(hours=i),
            status_code_id=status.value,
            specifier_id=requester_id,
        )

        session.add(friendship_status)

    session.commit()

    return expected_users
