from unittest.mock import MagicMock, patch
import pytest

from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)

from messenger.helpers.user_handler import UserHandler


@pytest.mark.parametrize(
    "criterion",
    [
        ((UserSchema.user_id == 632)),
        (
            (UserSchema.email == "some@email"),
            (UserSchema.first_name == "firstname"),
            (UserSchema.last_name == "last-name"),
        ),
        ((UserSchema.first_name == "name")),
    ],
)
@patch(
    "messenger.helpers.user_handler.UserHandler._get_record_with_not_found_raise"
)
def test_get_user(
    _get_record_with_not_found_raise_mock: MagicMock,
    mocker: MockerFixture,
    criterion,
):
    user_handler = UserHandler(mocker.MagicMock())

    expected_user = UserSchema()
    _get_record_with_not_found_raise_mock.return_value = expected_user

    user = user_handler.get_user(criterion)

    _get_record_with_not_found_raise_mock.assert_called_once_with(
        UserSchema, "no such user exists", criterion
    )
    assert user is expected_user
