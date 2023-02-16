from datetime import datetime, timedelta
from typing import Tuple
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests.conftest import (
    add_initial_friendship_status_codes,
    valid_usernames,
    valid_emails,
    valid_passwords,
)


friendship_status_codes = [
    FriendshipStatusCode.ACCEPTED,
    FriendshipStatusCode.DECLINED,
    FriendshipStatusCode.BLOCKED,
]


class TestSendFriendshipRequest:
    def add_user_to_friend_request(
        self,
        session: Session,
        requester_id: int,
        username: str,
        password: str,
        email: str,
    ):
        user_to_friend_request = UserSchema(
            user_id=requester_id + 1,
            username=username,
            password_hash=password,
            email=email,
        )

        session.add(user_to_friend_request)
        session.commit()
        session.refresh(user_to_friend_request)

        return user_to_friend_request

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_should_produce_201_on_success(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        user_to_friend_request = self.add_user_to_friend_request(
            session, current_active_user.user_id, username, password, email
        )

        response = test_client.post(
            f"friends/requests/send?username={user_to_friend_request.username}"
        )

        assert response.status_code == 201

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_should_create_friendship_request(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        user_to_friend_request = self.add_user_to_friend_request(
            session, current_active_user.user_id, username, password, email
        )

        test_client.post(
            f"friends/requests/send?username={user_to_friend_request.username}"
        )

        # if no friendship was created then this will throw an exception and test will fail
        session.query(FriendshipSchema).filter(
            FriendshipSchema.requester_id == current_active_user.user_id,
            FriendshipSchema.addressee_id == user_to_friend_request.user_id,
        ).one()

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_should_fail_when_friendship_request_already_sent(
        self,
        username: str,
        email: str,
        password: str,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        user_to_friend_request = self.add_user_to_friend_request(
            session, current_active_user.user_id, username, password, email
        )

        test_client.post(
            f"friends/requests/send?username={user_to_friend_request.username}"
        )

        response = test_client.post(
            f"friends/requests/send?username={user_to_friend_request.username}"
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "a friendship request was already sent"
        }

    @pytest.mark.parametrize(
        "friendship_status",
        friendship_status_codes,
    )
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_should_fail_when_friendship_exists(
        self,
        username: str,
        email: str,
        password: str,
        friendship_status: FriendshipStatusCode,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        user_to_friend_request = self.add_user_to_friend_request(
            session, current_active_user.user_id, username, password, email
        )

        friendship = FriendshipSchema(
            requester_id=current_active_user.user_id,
            addressee_id=user_to_friend_request.user_id,
            created_date_time=datetime.now() - timedelta(minutes=13),
        )
        friendship_status = FriendshipStatusSchema(
            requester_id=friendship.requester_id,
            addressee_id=friendship.addressee_id,
            status_code_id=friendship_status.value,
            specified_date_time=datetime.now() - timedelta(minutes=13),
            specifier_id=current_active_user.user_id,
        )

        session.add(friendship)
        session.add(friendship_status)

        session.commit()

        response = test_client.post(
            f"friends/requests/send?username={user_to_friend_request.username}"
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "you cannot send a friendship request"
        }

    def test_should_fail_when_sending_to_yourself(
        self,
        session: Session,
        client: Tuple[TestClient, UserSchema],
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        response = test_client.post(
            f"friends/requests/send?username={current_active_user.username}"
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "cannot send friendship request to yourself"
        }
