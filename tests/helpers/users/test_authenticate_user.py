from unittest.mock import MagicMock, patch
import pytest
from pytest_mock import MockerFixture
from argon2 import exceptions
from messenger_schemas.schema.user_schema import (
    UserSchema,
)

from messenger.helpers.users import authenticate_user
from tests.conftest import valid_emails, valid_passwords


@patch("messenger.helpers.users.UserHandler")
@patch("messenger.helpers.users.password_hasher")
class TestAuthenticateUser:
    @pytest.mark.parametrize(
        "email, password, password_hash",
        zip(
            valid_emails,
            valid_passwords,
            ["1", "2", "3", "5", "6", "7", "8", "02"],
        ),
    )
    def test_correctly_authenticates_user(
        self,
        password_hasher_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        email: str,
        password: str,
        password_hash: str,
    ):
        session_mock = mocker.MagicMock()
        expected_user = UserSchema(password_hash=password_hash)

        UserHandlerMock.return_value.get_user.return_value = expected_user
        password_hasher_mock.check_needs_rehash.return_value = False

        authenticated_user = authenticate_user(session_mock, password, email)

        # should verify password, check if it needs rehashing, and get the expected user.
        password_hasher_mock.verify.assert_called_once_with(
            password_hash, password
        )
        password_hasher_mock.check_needs_rehash.assert_called_once_with(
            password_hash
        )
        UserHandlerMock.return_value.get_user.assert_called_once()

        assert expected_user is authenticated_user

    @pytest.mark.parametrize(
        "email, password",
        zip(
            valid_emails,
            valid_passwords,
        ),
    )
    def test_when_no_user_found(
        self,
        _: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        email: str,
        password: str,
    ):
        session_mock = mocker.MagicMock()
        UserHandlerMock.return_value.get_user.return_value = None
        authenticated_user = authenticate_user(session_mock, password, email)

        assert authenticated_user is False

    @pytest.mark.parametrize(
        "email, password",
        zip(
            valid_emails,
            valid_passwords,
        ),
    )
    def test_password_verification_exceptions_caught(
        self,
        password_hasher_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        email: str,
        password: str,
    ):
        session_mock = mocker.MagicMock()
        UserHandlerMock.return_value.get_user.return_value = UserSchema()

        password_hasher_mock.verify.side_effect = exceptions.VerifyMismatchError
        authenticated_user = authenticate_user(session_mock, password, email)

        assert authenticated_user is False

        password_hasher_mock.verify.side_effect = exceptions.VerificationError
        authenticated_user = authenticate_user(session_mock, password, email)

        assert authenticated_user is False

        password_hasher_mock.verify.side_effect = exceptions.InvalidHash
        authenticated_user = authenticate_user(session_mock, password, email)

        assert authenticated_user is False

    @pytest.mark.parametrize(
        "email, password",
        zip(
            valid_emails,
            valid_passwords,
        ),
    )
    def test_when_password_needs_rehash(
        self,
        password_hasher_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        email: str,
        password: str,
    ):
        session_mock = mocker.MagicMock()
        expected_user = UserSchema()

        UserHandlerMock.return_value.get_user.return_value = expected_user
        password_hasher_mock.check_needs_rehash.return_value = True
        password_hasher_mock.hash.return_value = "new password hash"

        authenticated_user = authenticate_user(session_mock, password, email)

        # should rehash the password, add the new hash to the user schema,
        # and refresh the user record.
        password_hasher_mock.hash.assert_called_once_with(password)

        assert expected_user.password_hash == "new password hash"
        session_mock.refresh.assert_called_once_with(expected_user)
        assert expected_user is authenticated_user
