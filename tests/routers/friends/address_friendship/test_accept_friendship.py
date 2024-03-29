from typing import Tuple
from freezegun import freeze_time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.routers.friends.address_friendship.helpers.assertions import (
    assert_addressing_adds_new_friendship_status_to_db,
    assert_addressing_fails_when_friendship_already_addressed,
    assert_addressing_fails_when_friendship_blocked,
    assert_addressing_fails_when_friendship_not_found,
    assert_addressing_fails_when_user_not_found,
    assert_addressing_produces_201_status_code,
    assert_addressing_fails_when_current_user_is_not_addressee,
)
from tests.routers.friends.conftest import FROZEN_DATE
from tests.conftest import (
    valid_usernames,
    valid_emails,
    valid_passwords,
)


class TestAcceptFriendshipRequest:
    def get_url(self, username: str):
        return f"/friends/requests/accept?requester_username={username}"

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_it_adds_new_friendship_status_to_db(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        assert_addressing_adds_new_friendship_status_to_db(
            self.get_url(username),
            username,
            email,
            password,
            client,
            session,
            FriendshipStatusCode.ACCEPTED,
        )

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_response_status_code_is_201(
        self,
        username: str,
        email: str,
        password: str,
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
        )

    @pytest.mark.parametrize(
        "username",
        valid_usernames,
    )
    def test_when_no_user_found_should_fail(
        self,
        username: str,
        client: Tuple[TestClient, UserSchema],
    ):
        assert_addressing_fails_when_user_not_found(
            self.get_url(username),
            client,
        )

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_no_friendship_found_should_fail(
        self,
        username: str,
        password: str,
        email: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        assert_addressing_fails_when_friendship_not_found(
            self.get_url(username),
            username,
            password,
            email,
            client,
            session,
        )

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_already_addressed_should_fail(
        self,
        username: str,
        password: str,
        email: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        assert_addressing_fails_when_friendship_already_addressed(
            self.get_url(username),
            username,
            password,
            email,
            client,
            session,
        )

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_blocked_should_fail(
        self,
        username: str,
        password: str,
        email: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        assert_addressing_fails_when_friendship_blocked(
            self.get_url(username),
            username,
            password,
            email,
            client,
            session,
        )

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_current_active_user_not_addressee_should_fail(
        self,
        username: str,
        password: str,
        email: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        assert_addressing_fails_when_current_user_is_not_addressee(
            self.get_url(username),
            username,
            password,
            email,
            client,
            session,
        )
