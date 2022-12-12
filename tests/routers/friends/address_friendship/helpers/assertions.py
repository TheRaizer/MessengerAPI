from datetime import datetime, timedelta
from operator import attrgetter
from typing import Optional, Tuple
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
from tests.conftest import add_initial_friendship_status_codes
from tests.routers.friends.helpers.initialize_friendship_request import (
    initialize_friendship_request_addressed_to_current_user,
)


def assert_addressing_adds_new_friendship_status_to_db(
    url: str,
    username: str,
    email: str,
    password: str,
    client: Tuple[TestClient, UserSchema],
    session: Session,
    expected_friendship_status_code: FriendshipStatusCode,
    initial_friendship_status_code: Optional[FriendshipStatusCode] = None,
):
    (test_client, current_active_user) = client
    (
        friendship,
        friendship_requester,
    ) = initialize_friendship_request_addressed_to_current_user(
        session,
        current_active_user,
        username,
        email,
        password,
        initial_friendship_status_code,
    )

    test_client.post(url)

    session.refresh(friendship)

    latest_friendship_status = max(
        friendship.statuses,
        key=attrgetter("specified_date_time"),
    )

    assert (
        latest_friendship_status.status_code_id
        == expected_friendship_status_code.value
    )
    assert latest_friendship_status.requester_id == friendship_requester.user_id
    assert latest_friendship_status.addressee_id == current_active_user.user_id
    assert latest_friendship_status.specifier_id == current_active_user.user_id
    assert latest_friendship_status.specified_date_time == datetime.now()


def assert_addressing_produces_201_status_code(
    url: str,
    username: str,
    email: str,
    password: str,
    client: Tuple[TestClient, UserSchema],
    session: Session,
    initial_friendship_status_code: Optional[FriendshipStatusCode] = None,
):
    (test_client, current_active_user) = client

    initialize_friendship_request_addressed_to_current_user(
        session,
        current_active_user,
        username,
        email,
        password,
        initial_friendship_status_code,
    )

    response = test_client.post(url)

    assert response.status_code == 201


def assert_addressing_fails_when_user_not_found(
    url: str,
    client: Tuple[TestClient, UserSchema],
):
    # no requester user was added to the DB, so the request should fail
    (test_client, _) = client

    response = test_client.post(url)

    assert response.status_code == 404
    assert response.json() == {"detail": "no such user exists"}


def assert_addressing_fails_when_friendship_not_found(
    url: str,
    username: str,
    password: str,
    email: str,
    client: Tuple[TestClient, UserSchema],
    session: Session,
):
    (test_client, current_active_user) = client

    friendship_requester = UserSchema(
        user_id=current_active_user.user_id + 1,
        username=username,
        password_hash=password,
        email=email,
    )

    session.add(friendship_requester)
    session.commit()

    response = test_client.post(url)

    assert response.status_code == 404
    assert response.json() == {"detail": "friendship was not found"}


def assert_addressing_fails_when_friendship_already_addressed(
    url: str,
    username: str,
    password: str,
    email: str,
    client: Tuple[TestClient, UserSchema],
    session: Session,
):
    (test_client, current_active_user) = client

    (
        friendship,
        friendship_requester,
    ) = initialize_friendship_request_addressed_to_current_user(
        session, current_active_user, username, email, password
    )

    friendship.statuses.insert(
        0,
        FriendshipStatusSchema(
            requester_id=friendship_requester.user_id,
            addressee_id=current_active_user.user_id,
            specifier_id=current_active_user.user_id,
            status_code_id=FriendshipStatusCode.ACCEPTED.value,
            specified_date_time=datetime.now() + timedelta(days=10),
        ),
    )

    response = test_client.post(url)

    assert response.status_code == 400
    assert response.json() == {"detail": "friend request already addressed"}

    friendship.statuses.insert(
        0,
        FriendshipStatusSchema(
            requester_id=friendship_requester.user_id,
            addressee_id=current_active_user.user_id,
            specifier_id=current_active_user.user_id,
            status_code_id=FriendshipStatusCode.DECLINED.value,
            specified_date_time=datetime.now() + timedelta(days=11),
        ),
    )

    response = test_client.post(url)

    assert response.status_code == 400
    assert response.json() == {"detail": "friend request already addressed"}


def assert_addressing_fails_when_friendship_blocked(
    url: str,
    username: str,
    password: str,
    email: str,
    client: Tuple[TestClient, UserSchema],
    session: Session,
):
    (test_client, current_active_user) = client

    (
        friendship,
        friendship_requester,
    ) = initialize_friendship_request_addressed_to_current_user(
        session, current_active_user, username, email, password
    )

    friendship.statuses.insert(
        0,
        FriendshipStatusSchema(
            requester_id=friendship_requester.user_id,
            addressee_id=current_active_user.user_id,
            specifier_id=current_active_user.user_id,
            status_code_id=FriendshipStatusCode.BLOCKED.value,
            specified_date_time=datetime.now() + timedelta(days=10),
        ),
    )

    response = test_client.post(url)

    assert response.status_code == 400
    assert response.json() == {"detail": "friendship is blocked"}


def assert_addressing_fails_when_current_user_is_not_addressee(
    url: str,
    username: str,
    password: str,
    email: str,
    client: Tuple[TestClient, UserSchema],
    session: Session,
):
    (test_client, current_active_user) = client

    add_initial_friendship_status_codes(session)
    friendship_addressee = UserSchema(
        user_id=current_active_user.user_id + 1,
        username=username,
        password_hash=password,
        email=email,
    )
    friendship = FriendshipSchema(
        requester_id=current_active_user.user_id,
        addressee_id=friendship_addressee.user_id,
        created_date_time=datetime.now() - timedelta(minutes=13),
    )
    friendship_status = FriendshipStatusSchema(
        requester_id=friendship.requester_id,
        addressee_id=friendship.addressee_id,
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specified_date_time=datetime.now() - timedelta(minutes=13),
        specifier_id=friendship.requester_id,
    )

    session.add(friendship_addressee)
    session.add(friendship)
    session.add(friendship_status)
    session.commit()

    response = test_client.post(url)

    assert response.status_code == 404
    assert response.json() == {"detail": "friendship was not found"}
