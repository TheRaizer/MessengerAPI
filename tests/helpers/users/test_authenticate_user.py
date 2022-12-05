from unittest.mock import MagicMock, patch
import pytest
from pytest_mock import MockerFixture
from argon2 import exceptions
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)

from messenger.helpers.users import authenticate_user
from tests.helpers.conftest import valid_emails, valid_passwords


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
    def test_when_successful(
        self,
        password_hasher_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        email: str,
        password: str,
        password_hash: str,
    ):
        session_mock = mocker.MagicMock()
        user = UserSchema(password_hash=password_hash)

        UserHandlerMock.return_value.get_user.return_value = user
        password_hasher_mock.check_needs_rehash.return_value = False

        authenticated_user = authenticate_user(session_mock, password, email)

        UserHandlerMock.assert_called_once_with(session_mock)
        password_hasher_mock.verify.assert_called_once_with(
            password_hash, password
        )
        password_hasher_mock.check_needs_rehash.assert_called_once_with(
            password_hash
        )
        UserHandlerMock.return_value.get_user.assert_called_once()

        assert user is authenticated_user

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
        user = UserSchema()

        UserHandlerMock.return_value.get_user.return_value = user
        password_hasher_mock.check_needs_rehash.return_value = True
        password_hasher_mock.hash.return_value = "new password hash"

        authenticated_user = authenticate_user(session_mock, password, email)

        password_hasher_mock.hash.assert_called_once_with(password)

        assert user.password_hash == "new password hash"
        session_mock.refresh.assert_called_once_with(user)

        assert user is authenticated_user
