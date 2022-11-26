from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
import pytest
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.users import create_user
from .conftest import (
    valid_usernames,
    valid_passwords,
    valid_emails,
    invalid_usernames,
    invalid_passwords,
    invalid_emails,
)


class TestCreateUser:
    @pytest.mark.parametrize(
        "invalid_password, valid_email, valid_username",
        zip(invalid_passwords, valid_emails, valid_usernames),
    )
    def test_with_invalid_password(
        self,
        mocker: MockerFixture,
        invalid_password: str,
        valid_email: str,
        valid_username: str,
    ):
        session_mock = mocker.MagicMock()

        with pytest.raises(HTTPException):
            create_user(session_mock, invalid_password, valid_email, valid_username)

    @pytest.mark.parametrize(
        "valid_password, invalid_email, valid_username",
        zip(valid_passwords, invalid_emails, valid_usernames),
    )
    def test_with_invalid_emails(
        self,
        mocker: MockerFixture,
        valid_password: str,
        invalid_email: str,
        valid_username: str,
    ):
        session_mock = mocker.MagicMock()

        with pytest.raises(HTTPException):
            create_user(session_mock, valid_password, invalid_email, valid_username)

    @pytest.mark.parametrize(
        "valid_password, valid_email, invalid_username",
        zip(valid_passwords, valid_emails, invalid_usernames),
    )
    def test_with_invalid_username(
        self,
        mocker: MockerFixture,
        valid_password: str,
        valid_email: str,
        invalid_username: str,
    ):
        session_mock = mocker.MagicMock()

        with pytest.raises(HTTPException):
            create_user(session_mock, valid_password, valid_email, invalid_username)

    @patch("messenger.helpers.auth.is_username_valid.UserHandler.get_user")
    def test_it_fails_on_existent_username(
        self, get_user_mock: MagicMock, mocker: MockerFixture
    ):
        session_mock = mocker.MagicMock()

        get_user_mock.return_value = UserSchema(
            username="username", password_hash="hash", email="email"
        )

        with pytest.raises(HTTPException):
            create_user(
                session_mock,
                valid_passwords[1],
                valid_emails[1],
                valid_usernames[0],
            )

    @patch("messenger.helpers.auth.is_email_valid.UserHandler.get_user")
    @patch("messenger.helpers.users.is_username_valid")
    def test_it_fails_on_existent_email(
        self,
        is_username_valid_mock: MagicMock,
        get_user_mock: MagicMock,
        mocker: MockerFixture,
    ):
        session_mock = mocker.MagicMock()
        is_username_valid_mock.return_value = True
        get_user_mock.return_value = UserSchema(
            username="username", password_hash="hash", email="email"
        )

        with pytest.raises(HTTPException):
            create_user(
                session_mock,
                valid_passwords[1],
                valid_emails[0],
                valid_usernames[1],
            )

    @pytest.mark.parametrize(
        "valid_password, valid_email, valid_username",
        zip(valid_passwords, valid_emails, valid_usernames),
    )
    @patch("messenger.helpers.auth.is_email_valid.UserHandler.get_user")
    @patch("messenger.helpers.auth.is_username_valid.UserHandler.get_user")
    @patch("messenger.helpers.users.password_hasher")
    def test_it_adds_user_to_db(
        self,
        password_hasher_mock: MagicMock,
        username_get_user_mock: MagicMock,
        email_get_user_mock: MagicMock,
        valid_password: str,
        valid_email: str,
        valid_username: str,
        mocker: MockerFixture,
    ):
        session_mock = mocker.MagicMock()

        # raises exception so that no existent usernames or emails are found
        username_get_user_mock.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )
        email_get_user_mock.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )

        # mock the hasher so no hashing actually occurs
        password_hasher_mock.hash = lambda password: password

        created_user = create_user(
            session_mock, valid_password, valid_email, valid_username
        )

        # user should be created with the correct values
        assert created_user.username == valid_username
        assert created_user.email == valid_email
        assert created_user.password_hash == valid_password

        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()
        session_mock.refresh.assert_called_once()
