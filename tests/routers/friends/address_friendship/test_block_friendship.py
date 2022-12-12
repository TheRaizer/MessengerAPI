from datetime import datetime
from operator import attrgetter
from typing import Tuple
from freezegun import freeze_time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from tests.routers.friends.address_friendship.helpers.assertions import (
    assert_addressing_adds_new_friendship_status_to_db,
    assert_addressing_produces_201_status_code,
)
from tests.routers.friends.helpers.initialize_friendship_request import (
    initialize_friendship_request_addressed_to_current_user,
)
from tests.routers.friends.conftest import FROZEN_DATE
from tests.conftest import (
    add_initial_friendship_status_codes,
    valid_usernames,
    valid_emails,
    valid_passwords,
)

friendship_status_codes = [
    FriendshipStatusCode.ACCEPTED,
    FriendshipStatusCode.DECLINED,
    FriendshipStatusCode.REQUESTED,
]


class TestBlockFriendship:
    def get_url(self, username: str):
        return f"/friends/requests/block?user_to_block_username={username}"

    def add_user_to_block(
        self,
        session: Session,
        blocker_id: int,
        username: str,
        password: str,
        email: str,
    ):
        user_to_block = UserSchema(
            user_id=blocker_id + 1,
            username=username,
            password_hash=password,
            email=email,
        )

        session.add(user_to_block)
        session.commit()
        session.refresh(user_to_block)

        return user_to_block

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "initial_friendship_status",
        friendship_status_codes,
    )
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_exists_should_add_block_status(
        self,
        username: str,
        email: str,
        password: str,
        initial_friendship_status: FriendshipStatusCode,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        assert_addressing_adds_new_friendship_status_to_db(
            self.get_url(username),
            username,
            email,
            password,
            client,
            session,
            FriendshipStatusCode.BLOCKED,
            initial_friendship_status,
        )

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "initial_friendship_status",
        friendship_status_codes,
    )
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_response_status_code_is_201(
        self,
        username: str,
        email: str,
        password: str,
        initial_friendship_status: FriendshipStatusCode,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        assert_addressing_produces_201_status_code(
            self.get_url(username),
            username,
            email,
            password,
            client,
            session,
            initial_friendship_status,
        )

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_does_not_exists_should_create_friendship(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        user_to_block = self.add_user_to_block(
            session, current_active_user.user_id, username, password, email
        )
        test_client.post(self.get_url(username))

        # if no friendship was created then this will throw an exception and test will fail
        session.query(FriendshipSchema).filter(
            FriendshipSchema.requester_id == current_active_user.user_id,
            FriendshipSchema.addressee_id == user_to_block.user_id,
        ).one()

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_does_not_exists_should_add_blocked_status(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        user_to_block = self.add_user_to_block(
            session, current_active_user.user_id, username, password, email
        )
        test_client.post(self.get_url(username))

        expected_friendship: FriendshipSchema = (
            session.query(FriendshipSchema)
            .filter(
                FriendshipSchema.requester_id == current_active_user.user_id,
                FriendshipSchema.addressee_id == user_to_block.user_id,
            )
            .one()
        )

        latest_friendship_status = max(
            expected_friendship.statuses,
            key=attrgetter("specified_date_time"),
        )

        assert (
            latest_friendship_status.status_code_id
            == FriendshipStatusCode.BLOCKED.value
        )
        assert (
            latest_friendship_status.specifier_id == current_active_user.user_id
        )
        assert latest_friendship_status.specified_date_time == datetime.now()
        assert latest_friendship_status.addressee_id == user_to_block.user_id

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_does_not_exists_response_status_is_201(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        self.add_user_to_block(
            session, current_active_user.user_id, username, password, email
        )

        response = test_client.post(self.get_url(username))

        assert response.status_code == 201

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_route_fails_when_already_blocked(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        initialize_friendship_request_addressed_to_current_user(
            session,
            current_active_user,
            username,
            email,
            password,
            FriendshipStatusCode.BLOCKED,
        )
        response = test_client.post(self.get_url(username))

        assert response.status_code == 400
        assert response.json() == {"detail": "friendship is blocked"}
