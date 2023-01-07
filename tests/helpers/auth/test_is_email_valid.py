from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
import pytest
from messenger.constants.auth_details import EmailError
from messenger.helpers.auth.is_email_valid import is_email_valid
from tests.conftest import (
    valid_emails,
    invalid_emails,
)
from tests.helpers.auth.conftest import test_user_records


class TestIsEmailValid:
    @pytest.mark.parametrize(
        "email",
        valid_emails,
    )
    @patch("messenger.helpers.auth.is_email_valid.UserHandler.get_user")
    def test_with_valid_email(self, get_user_mock: MagicMock, email: str):
        get_user_mock.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )
        validity_data = is_email_valid(MagicMock(), email)

        assert validity_data.is_valid is True
        assert validity_data.detail is None

    @pytest.mark.parametrize(
        "email",
        invalid_emails,
    )
    @patch("messenger.helpers.auth.is_email_valid.UserHandler.get_user")
    def test_with_invalid_email(self, get_user_mock: MagicMock, email: str):
        get_user_mock.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )
        validity_data = is_email_valid(MagicMock(), email)

        assert validity_data.is_valid is False
        assert validity_data.detail == EmailError.INVALID_EMAIL.value

    @pytest.mark.parametrize(
        "email",
        valid_emails,
    )
    @patch("messenger.helpers.auth.is_email_valid.UserHandler.get_user")
    def test_with_email_that_already_exists(
        self, get_user_mock: MagicMock, email: str
    ):
        get_user_mock.return_value = test_user_records[0]
        validity_data = is_email_valid(MagicMock(), email)

        assert validity_data.is_valid is False
        assert validity_data.detail == EmailError.ACCOUNT_EXISTS.value
