from datetime import datetime, timedelta
from fastapi import HTTPException
from freezegun import freeze_time

import pytest
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from messenger.friends.friendship_handler import FriendshipHandler, address_friendship_request

# the date that the initial records will be added at
FROZEN_DATE = "2022-11-07"


@freeze_time(FROZEN_DATE)
def test_get_latest_friendship_status(
    mocker: MockerFixture,
):
    status = FriendshipStatusSchema(
        requester_id=1,
        addressee_id=2,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=1,
    )

    friendship_handler = FriendshipHandler(mocker.MagicMock(), FriendshipSchema())

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
def test_raise_if_blocked(mocker: MockerFixture):
    friendship = FriendshipSchema()
    friendship.statuses = [
        FriendshipStatusSchema(
            requester_id=1,
            addressee_id=2,
            specified_date_time=datetime.now(),
            status_code_id=FriendshipStatusCode.REQUESTED.value,
            specifier_id=1,
        )
    ]

    friendship_handler = FriendshipHandler(mocker.MagicMock(), friendship)

    # should run without raising since friendship is initialized with requested status
    friendship_handler.raise_if_blocked()

    status = FriendshipStatusSchema(
        requester_id=1,
        addressee_id=2,
        specified_date_time=datetime.now() + timedelta(days=1),
        status_code_id=FriendshipStatusCode.BLOCKED.value,
        specifier_id=2,
    )

    assert friendship_handler.friendship is not None

    friendship_handler.friendship.statuses.append(status)

    # should raise now that the friendship has a new status with a blocked status code
    with pytest.raises(HTTPException):
        friendship_handler.raise_if_blocked()


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

        with pytest.raises(HTTPException):
            address_friendship_request(
                friendship_handler, FriendshipStatusCode.DECLINED
            )

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

        with pytest.raises(HTTPException):
            address_friendship_request(
                friendship_handler, FriendshipStatusCode.DECLINED
            )

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

        with pytest.raises(HTTPException):
            address_friendship_request(
                friendship_handler, FriendshipStatusCode.DECLINED
            )
