from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from freezegun import freeze_time

import pytest
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from messenger.helpers.friends import (
    FriendshipHandler,
)
from tests.helpers.friends import FROZEN_DATE


class TestRaiseIfBlocked:
    @freeze_time(FROZEN_DATE)
    @patch(
        "messenger.helpers.friends.FriendshipHandler.get_latest_friendship_status"
    )
    def test_when_friendship_blocked(
        self,
        get_latest_friendship_status_mock: MagicMock,
        mocker: MockerFixture,
    ):
        friendship_handler = FriendshipHandler(mocker.MagicMock())

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

    @freeze_time(FROZEN_DATE)
    @pytest.mark.parametrize(
        "status_code_id_no_raise",
        [
            FriendshipStatusCode.REQUESTED.value,
            FriendshipStatusCode.ACCEPTED.value,
            FriendshipStatusCode.DECLINED.value,
        ],
    )
    @patch(
        "messenger.helpers.friends.FriendshipHandler.get_latest_friendship_status"
    )
    def test_when_friendship_not_blocked(
        self,
        get_latest_friendship_status_mock: MagicMock,
        mocker: MockerFixture,
        status_code_id_no_raise: str,
    ):
        get_latest_friendship_status_mock.return_value = FriendshipStatusSchema(
            requester_id=1,
            addressee_id=2,
            specified_date_time=datetime.now(),
            status_code_id=status_code_id_no_raise,
            specifier_id=1,
        )

        friendship_handler = FriendshipHandler(mocker.MagicMock())

        # should run without raising since friendship is not blocked in all cases
        friendship_handler.raise_if_blocked()
