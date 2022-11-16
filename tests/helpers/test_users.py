from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import pytest
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.users import create_user

valid_usernames = ["hi_iamusername", "some_other_username", "bob231", "hellothere2"]
invalid_usernames = [
    "_invalid",
    "bob__23",
    "tim#2",
    "a",
    "this_username_is_way_too_long_to_be_acceptable",
]

valid_passwords = [
    "AValidPassword23",
    "AnotherValid23Password",
    "23Valid**Pass",
    "//Valid/'Pass2332",
]
invalid_passwords = [
    "Test1ng",
    "notavalidpassword23",
    "notAvalidpassword",
    "23322122awds",
    "invalidpassword",
    "23212",
    "NOTVALID",
]

valid_emails = [
    "email@email.com",
    "something@email.com",
    "my.ownsite@ourearth.org",
    "aperson@gmail.com",
]
invalid_emails = ["@email.com", "cool.cool", "not an email", "google.email@com"]


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

    @patch("messenger.helpers.auth.UserHandler.get_user")
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

    @patch("messenger.helpers.auth.UserHandler.get_user")
    def test_it_fails_on_existent_email(
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
                valid_emails[0],
                valid_usernames[1],
            )

    @pytest.mark.parametrize(
        "valid_password, valid_email, valid_username",
        zip(valid_passwords, valid_emails, valid_usernames),
    )
    @patch("messenger.helpers.auth.UserHandler.get_user")
    @patch("messenger.helpers.users.password_hasher")
    def test_it_adds_user_to_db(
        self,
        password_hasher_mock: MagicMock,
        get_user_mock: MagicMock,
        mocker: MockerFixture,
        valid_password: str,
        valid_email: str,
        valid_username: str,
    ):
        session_mock = mocker.MagicMock()

        # set to none so that no exceptions are raised due to an existent email or username
        get_user_mock.return_value = None

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
