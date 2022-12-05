from datetime import datetime, timedelta
from operator import attrgetter
from typing import Tuple
from unittest.mock import MagicMock, patch
from freezegun import freeze_time
import pytest
from fastapi.testclient import TestClient
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
from tests.routers.friends.conftest import FROZEN_DATE
from tests.conftest import (
    add_initial_friendship_status_codes,
    valid_usernames,
    valid_emails,
    valid_passwords,
)


class TestAddressingFriendship:
    def initialize_friendship_request(
        self,
        session: Session,
        current_active_user: UserSchema,
        username: str,
        email: str,
        password: str,
    ):
        add_initial_friendship_status_codes(session)
        friendship_requester = UserSchema(
            user_id=current_active_user.user_id + 1,
            username=username,
            password_hash=password,
            email=email,
        )
        friendship = FriendshipSchema(
            requester_id=friendship_requester.user_id,
            addressee_id=current_active_user.user_id,
            created_date_time=datetime.now() - timedelta(minutes=13),
        )
        friendship_status = FriendshipStatusSchema(
            requester_id=friendship_requester.user_id,
            addressee_id=current_active_user.user_id,
            status_code_id=FriendshipStatusCode.REQUESTED.value,
            specified_date_time=datetime.now() - timedelta(minutes=13),
            specifier_id=friendship_requester.user_id,
        )

        session.add(friendship_requester)
        session.add(friendship)
        session.add(friendship_status)

        session.commit()

        return (friendship, friendship_requester)

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_accept_friendship_request(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client

        (friendship, friendship_requester) = self.initialize_friendship_request(
            session, current_active_user, username, email, password
        )

        response = test_client.post(
            f"/friends/requests/accept?requester_username={username}"
        )

        session.refresh(friendship)

        added_friendship_status = max(
            friendship.statuses,
            key=attrgetter("specified_date_time"),
        )

        assert (
            added_friendship_status.status_code_id
            == FriendshipStatusCode.ACCEPTED.value
        )
        assert (
            added_friendship_status.requester_id == friendship_requester.user_id
        )
        assert (
            added_friendship_status.addressee_id == current_active_user.user_id
        )
        assert (
            added_friendship_status.specifier_id == current_active_user.user_id
        )
        assert added_friendship_status.specified_date_time == datetime.now()
        assert response.status_code == 201

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_decline_friendship_request(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client

        (friendship, friendship_requester) = self.initialize_friendship_request(
            session, current_active_user, username, email, password
        )

        response = test_client.post(
            f"/friends/requests/decline?requester_username={username}"
        )

        session.refresh(friendship)

        added_friendship_status = max(
            friendship.statuses,
            key=attrgetter("specified_date_time"),
        )

        assert (
            added_friendship_status.status_code_id
            == FriendshipStatusCode.DECLINED.value
        )
        assert (
            added_friendship_status.requester_id == friendship_requester.user_id
        )
        assert (
            added_friendship_status.addressee_id == current_active_user.user_id
        )
        assert (
            added_friendship_status.specifier_id == current_active_user.user_id
        )
        assert added_friendship_status.specified_date_time == datetime.now()
        assert response.status_code == 201
