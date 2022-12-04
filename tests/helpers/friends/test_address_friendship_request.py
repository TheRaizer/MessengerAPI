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

from messenger.helpers.friends import (
    FriendshipHandler,
    address_friendship_request,
)
from tests.helpers.friends import FROZEN_DATE


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
