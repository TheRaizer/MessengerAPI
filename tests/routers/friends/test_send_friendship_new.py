from datetime import datetime
from typing import Tuple
import json
from fastapi.testclient import TestClient
from freezegun import freeze_time
import pytest
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.models.friendship_model import FriendshipModel
from tests.conftest import (
    add_initial_friendship_status_codes,
    valid_usernames,
    valid_emails,
    valid_passwords,
)
from tests.routers.friends.conftest import FROZEN_DATE
from tests.routers.friends.helpers.initialize_friendship_request import (
    initialize_friendship_request,
)


friendship_status_codes = [
    FriendshipStatusCode.ACCEPTED,
    FriendshipStatusCode.DECLINED,
    FriendshipStatusCode.BLOCKED,
]


@freeze_time(FROZEN_DATE)
class TestSendFriendship:
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_successfully_adds_new_friendship_request(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        addressee = UserSchema(
            user_id=current_active_user.user_id + 1,
            username=username,
            email=email,
            password_hash=password,
        )

        session.add(addressee)

        session.commit()
        test_client.post(f"/friends/requests/send-request?username={username}")

        assert len(current_active_user.friend_requests_sent) == 1

        friendship_request = current_active_user.friend_requests_sent[0]

        assert friendship_request.addressee_id == addressee.user_id
        assert friendship_request.requester_id == current_active_user.user_id

        friendship_status_code = friendship_request.statuses[0]

        assert (
            friendship_status_code.status_code_id
            == FriendshipStatusCode.REQUESTED.value
        )
        assert friendship_request.created_date_time == datetime.now()
        assert friendship_status_code.specified_date_time == datetime.now()
        assert (
            friendship_status_code.specifier_id == current_active_user.user_id
        )

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_response_code_is_201_on_success(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)
        session.add(
            UserSchema(
                user_id=current_active_user.user_id + 1,
                username=username,
                email=email,
                password_hash=password,
            )
        )

        session.commit()

        response = test_client.post(
            f"/friends/requests/send-request?username={username}"
        )

        assert response.status_code == 201

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_successfully_returns_friendship_model(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        add_initial_friendship_status_codes(session)

        addressee = UserSchema(
            user_id=current_active_user.user_id + 1,
            username=username,
            email=email,
            password_hash=password,
        )

        session.add(addressee)

        session.commit()
        response = test_client.post(
            f"/friends/requests/send-request?username={username}"
        )

        # parsing to and from json converts the frozen date time
        # to one that allows correct comparison
        assert response.json() == json.loads(
            FriendshipModel(
                requester_id=current_active_user.user_id,
                addressee_id=addressee.user_id,
                created_date_time=datetime.now(),
            ).json()
        )

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_already_requested(
        self,
        username: str,
        email: str,
        password: str,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        initialize_friendship_request(
            session, current_active_user, username, email, password
        )

        response = test_client.post(
            f"/friends/requests/send-request?username={username}"
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "a friendship request was already sent"
        }

    @pytest.mark.parametrize(
        "initial_friendship_status_code", friendship_status_codes
    )
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_friendship_already_addressed(
        self,
        username: str,
        email: str,
        password: str,
        initial_friendship_status_code: FriendshipStatusCode,
        client: Tuple[TestClient, UserSchema],
        session: Session,
    ):
        (test_client, current_active_user) = client
        initialize_friendship_request(
            session,
            current_active_user,
            username,
            email,
            password,
            initial_friendship_status_code,
        )

        response = test_client.post(
            f"/friends/requests/send-request?username={username}"
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "you cannot send a friendship request"
        }
