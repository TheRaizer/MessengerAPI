from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from freezegun import freeze_time
from sqlalchemy.orm import Session
import pytest
from pytest_mock import MockerFixture
from messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from messenger.helpers.handlers.friendship_handler import (
    FriendshipHandler,
)
from tests.helpers.friends import FROZEN_DATE


@freeze_time(FROZEN_DATE)
def test_get_latest_friendship_status(mocker: MockerFixture):
    status = FriendshipStatusSchema(
        requester_id=1,
        addressee_id=2,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=1,
    )

    friendship_handler = FriendshipHandler(
        mocker.MagicMock(), FriendshipSchema()
    )

    assert friendship_handler.friendship is not None

    friendship_handler.friendship.statuses = [status]

    latest_status = friendship_handler.get_latest_friendship_status()

    assert latest_status == status

    status = FriendshipStatusSchema(
        requester_id=1,
        addressee_id=2,
        specified_date_time=datetime.now() + timedelta(days=10),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=1,
    )

    friendship_handler.friendship.statuses.append(status)
    latest_status = friendship_handler.get_latest_friendship_status()

    assert latest_status == status


# TODO: add some negative test params
@freeze_time(FROZEN_DATE)
@pytest.mark.parametrize(
    "user_a_id, user_b_id",
    [(1, 3), (4, 2), (12, 1223), (11, 93), (98, 11)],
)
def test_get_friendship_bidirectional_query(
    user_a_id: int,
    user_b_id: int,
    session: Session,
):
    friendship_handler = FriendshipHandler(session)

    user_a = UserSchema(
        user_id=user_a_id,
        username=f"username_{user_a_id}",
        email=f"email_{user_a_id}",
        password_hash="password",
    )
    user_b = UserSchema(
        user_id=user_b_id,
        username=f"username_{user_b_id}",
        email=f"email_{user_b_id}",
        password_hash="password",
    )

    friendship = FriendshipSchema(
        requester_id=user_a_id,
        addressee_id=user_b_id,
        created_date_time=datetime.now(),
    )

    session.add(user_a)
    session.add(user_b)
    session.add(friendship)
    session.commit()

    friendship_handler.get_friendship_bidirectional_query(
        user_a.user_id, user_b.user_id
    )

    assert friendship_handler.friendship == friendship


@freeze_time(FROZEN_DATE)
@pytest.mark.parametrize(
    "requester_id, addressee_id, specifier_id, new_status_code_id",
    [
        (1, 5, 1, FriendshipStatusCode.REQUESTED),
        (121, 332, 332, FriendshipStatusCode.ACCEPTED),
        (446, 2213, 446, FriendshipStatusCode.DECLINED),
        (4, 0, 4, FriendshipStatusCode.BLOCKED),
    ],
)
@patch("messenger.helpers.handlers.friendship_handler.FriendshipStatusSchema")
def test_add_new_status(
    FriendshipStatusSchemaMock: MagicMock,
    mocker: MockerFixture,
    requester_id: int,
    addressee_id: int,
    specifier_id: int,
    new_status_code_id: FriendshipStatusCode,
):
    session_mock = mocker.MagicMock()
    friendship_handler = FriendshipHandler(session_mock)

    kwargs = {
        "requester_id": requester_id,
        "addressee_id": addressee_id,
        "specified_date_time": datetime.now(),
        "status_code_id": new_status_code_id.value,
        "specifier_id": specifier_id,
    }

    expected_friendship_status = FriendshipStatusSchema(**kwargs)
    FriendshipStatusSchemaMock.return_value = expected_friendship_status

    new_status = friendship_handler.add_new_status(
        requester_id, addressee_id, specifier_id, new_status_code_id
    )

    FriendshipStatusSchemaMock.assert_called_once_with(**kwargs)

    session_mock.add.assert_called_once_with(expected_friendship_status)

    assert new_status is expected_friendship_status
