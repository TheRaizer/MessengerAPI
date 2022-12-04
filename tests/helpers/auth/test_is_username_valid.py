from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
import pytest
from messenger.constants.auth_details import UsernameError
from messenger.helpers.auth.is_username_valid import is_username_valid
from tests.helpers.conftest import (
    valid_usernames,
    invalid_usernames,
)
from tests.helpers.auth import test_user_records


class TestIsUsernameValid:
    @pytest.mark.parametrize(
        "username",
        valid_usernames,
    )
    @patch("messenger.helpers.auth.is_username_valid.UserHandler.get_user")
    def test_valid_username(self, get_user_mock: MagicMock, username: str):
        get_user_mock.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )
        validity_data = is_username_valid(MagicMock(), username)

        assert validity_data.is_valid is True
        assert validity_data.detail is None

    @pytest.mark.parametrize(
        "username",
        invalid_usernames,
    )
    @patch("messenger.helpers.auth.is_username_valid.UserHandler.get_user")
    def test_invalid_username(self, get_user_mock: MagicMock, username: str):
        get_user_mock.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )
        validity_data = is_username_valid(MagicMock(), username)

        assert validity_data.is_valid is False
        assert validity_data.detail == UsernameError.INVALID_USERNAME.value

    @pytest.mark.parametrize(
        "username",
        valid_usernames,
    )
    @patch("messenger.helpers.auth.is_username_valid.UserHandler.get_user")
    def test_username_exists(self, get_user_mock: MagicMock, username: str):
        get_user_mock.return_value = test_user_records[0]
        validity_data = is_username_valid(MagicMock(), username)

        assert validity_data.is_valid is False
        assert validity_data.detail == UsernameError.USERNAME_TAKEN.value
