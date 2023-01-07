from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from freezegun import freeze_time

import pytest
from pytest_mock import MockerFixture
from messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from messenger.helpers.handlers.friendship_handler import (
    FriendshipHandler,
)
from messenger.helpers.address_friendship_request import (
    address_friendship_request,
)
from tests.helpers.friends import FROZEN_DATE


class TestAddressFriendshipRequest:
    @freeze_time(FROZEN_DATE)
    @patch(
        "messenger.helpers.handlers.friendship_handler.FriendshipStatusSchema"
    )
    def test_adds_new_accepted_status(
        self, FriendshipStatusSchemaMock: MagicMock, mocker: MockerFixture
    ):
        db_mock = mocker.MagicMock()
        friendship = FriendshipSchema(
            requester_id=1, addressee_id=2, created_date_time=datetime.now()
        )

        friendship_handler = FriendshipHandler(db_mock, friendship)
        address_friendship_request(
            friendship_handler, FriendshipStatusCode.ACCEPTED
        )

        db_mock.add.assert_called_with(FriendshipStatusSchemaMock.return_value)
        FriendshipStatusSchemaMock.assert_called_once_with(
            requester_id=friendship.requester_id,
            addressee_id=friendship.addressee_id,
            specified_date_time=datetime.now(),
            status_code_id=FriendshipStatusCode.ACCEPTED.value,
            specifier_id=friendship.addressee_id,
        )

    @freeze_time(FROZEN_DATE)
    @patch(
        "messenger.helpers.handlers.friendship_handler.FriendshipStatusSchema"
    )
    def test_adds_new_declined_status(
        self,
        FriendshipStatusSchemaMock: MagicMock,
        mocker: MockerFixture,
    ):
        db_mock = mocker.MagicMock()
        friendship = FriendshipSchema(
            requester_id=12, addressee_id=21, created_date_time=datetime.now()
        )
        friendship_handler = FriendshipHandler(db_mock, friendship)
        address_friendship_request(
            friendship_handler, FriendshipStatusCode.DECLINED
        )

        db_mock.add.assert_called_with(FriendshipStatusSchemaMock.return_value)
        FriendshipStatusSchemaMock.assert_called_once_with(
            requester_id=friendship.requester_id,
            addressee_id=friendship.addressee_id,
            specified_date_time=datetime.now(),
            status_code_id=FriendshipStatusCode.DECLINED.value,
            specifier_id=friendship.addressee_id,
        )

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
