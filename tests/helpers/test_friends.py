from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from freezegun import freeze_time

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import and_, or_
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

from messenger.helpers.friends import (
    FriendshipHandler,
    address_friendship_request,
)

# the date that the initial records will be added at
FROZEN_DATE = "2022-11-07"


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


@freeze_time(FROZEN_DATE)
@patch(
    "messenger.helpers.friends.FriendshipHandler.get_latest_friendship_status"
)
def test_raise_if_blocked(
    get_latest_friendship_status_mock: MagicMock, mocker: MockerFixture
):
    get_latest_friendship_status_mock.return_value = FriendshipStatusSchema(
        requester_id=1,
        addressee_id=2,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=1,
    )

    friendship_handler = FriendshipHandler(mocker.MagicMock())

    # should run without raising since friendship is initialized with requested status
    friendship_handler.raise_if_blocked()

    get_latest_friendship_status_mock.return_value = FriendshipStatusSchema(
        requester_id=1,
        addressee_id=2,
        specified_date_time=datetime.now() + timedelta(days=1),
        status_code_id=FriendshipStatusCode.BLOCKED.value,
        specifier_id=2,
    )

    # should raise now that the friendship has a new status with a blocked status code
    with pytest.raises(HTTPException) as exc:
        friendship_handler.raise_if_blocked()
        assert exc.value.status_code == 400
        assert exc.value.detail == "friendship is blocked"


@patch(
    "messenger.helpers.friends.FriendshipHandler._get_record_with_not_found_raise"
)
@patch("messenger.helpers.friends.and_")
@patch("messenger.helpers.friends.or_")
def test_get_friendship_bidirectional_query(
    or_mock: MagicMock,
    and_mock: MagicMock,
    _get_record_with_not_found_raise_mock: MagicMock,
    mocker: MockerFixture,
):
    DETAIL = "friendship was not found"
    friendship_handler = FriendshipHandler(mocker.MagicMock())

    user_a = UserSchema(user_id=1)
    user_b = UserSchema(user_id=2)

    friendship = FriendshipSchema(requester_id=1, addressee_id=2)

    _get_record_with_not_found_raise_mock.return_value = friendship

    and_mock_return = "and_filter"
    and_mock.return_value.self_group.return_value = and_mock_return

    or_mock_return = "or_filter"
    or_mock.return_value = or_mock_return

    friendship_handler.get_friendship_bidirectional_query(user_a, user_b)

    assert friendship_handler.friendship == friendship
    assert and_mock.call_count == 2

    or_mock.assert_called_once_with(
        *[
            and_mock_return,
            and_mock_return,
        ]
    )

    _get_record_with_not_found_raise_mock.assert_called_once_with(
        FriendshipSchema, DETAIL, or_mock_return
    )

    _get_record_with_not_found_raise_mock.side_effect = HTTPException(
        status_code=404, detail=DETAIL
    )

    with (pytest.raises(HTTPException) as exc):
        friendship_handler.get_friendship_bidirectional_query(user_a, user_b)
        assert exc.value.status_code == 404
        assert exc.value.detail == DETAIL
        assert friendship_handler.friendship is None


class TestAddressFriendshipRequest:
    @freeze_time(FROZEN_DATE)
    def test_adds_new_accepted_status(self, mocker: MockerFixture):
        friendship_handler = FriendshipHandler(
            mocker.MagicMock(),
            FriendshipSchema(
                requester_id=1, addressee_id=2, created_date_time=datetime.now()
            ),
        )
        new_status = address_friendship_request(
            friendship_handler, FriendshipStatusCode.ACCEPTED
        )

        assert new_status.status_code_id == FriendshipStatusCode.ACCEPTED.value

    @freeze_time(FROZEN_DATE)
    def test_adds_new_declined_status(self, mocker: MockerFixture):
        friendship_handler = FriendshipHandler(
            mocker.MagicMock(),
            FriendshipSchema(
                requester_id=1, addressee_id=2, created_date_time=datetime.now()
            ),
        )
        new_status = address_friendship_request(
            friendship_handler, FriendshipStatusCode.DECLINED
        )

        assert new_status.status_code_id == FriendshipStatusCode.DECLINED.value

    def test_raises_when_friendship_blocked(self, mocker: MockerFixture):
        friendship = FriendshipSchema(
            requester_id=1, addressee_id=2, created_date_time=datetime.now()
        )

        friendship.statuses = [
            FriendshipStatusSchema(
                requester_id=1,
                addressee_id=2,
                specified_date_time=datetime.now(),
                status_code_id=FriendshipStatusCode.BLOCKED.value,
                specifier_id=2,
            )
        ]
        friendship_handler = FriendshipHandler(mocker.MagicMock(), friendship)

        with pytest.raises(HTTPException) as exc:
            address_friendship_request(
                friendship_handler, FriendshipStatusCode.DECLINED
            )
            assert exc.value.status_code == 400
            assert exc.value.detail == "friendship is blocked"

    def test_raises_when_friendship_addressed(self, mocker: MockerFixture):
        friendship = FriendshipSchema(
            requester_id=1, addressee_id=2, created_date_time=datetime.now()
        )

        friendship.statuses = [
            FriendshipStatusSchema(
                requester_id=1,
                addressee_id=2,
                specified_date_time=datetime.now(),
                status_code_id=FriendshipStatusCode.ACCEPTED.value,
                specifier_id=2,
            )
        ]
        friendship_handler = FriendshipHandler(mocker.MagicMock(), friendship)

        with pytest.raises(HTTPException) as exc:
            address_friendship_request(
                friendship_handler, FriendshipStatusCode.DECLINED
            )
            assert exc.value.status_code == 400
            assert exc.value.detail == "friend request already addressed"

        assert friendship_handler.friendship is not None
        friendship_handler.friendship.statuses = [
            FriendshipStatusSchema(
                requester_id=1,
                addressee_id=2,
                specified_date_time=datetime.now() + timedelta(days=1),
                status_code_id=FriendshipStatusCode.DECLINED.value,
                specifier_id=2,
            )
        ]

        with pytest.raises(HTTPException) as exc:
            address_friendship_request(
                friendship_handler, FriendshipStatusCode.DECLINED
            )
            assert exc.value.status_code == 400
            assert exc.value.detail == "friend request already addressed"
