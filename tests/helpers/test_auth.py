from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from freezegun import freeze_time
import pytest
from jose import ExpiredSignatureError, JWTError, jwt
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.auth_details import EmailError, UsernameError
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth.auth_token import (
    ALGORITHM,
    LOGIN_TOKEN_EXPIRE_MINUTES,
    TokenData,
    create_access_token,
    create_login_token,
)
from messenger.helpers.auth.is_email_valid import is_email_valid

from messenger.helpers.auth.is_password_valid import is_password_valid
from messenger.helpers.auth.is_username_valid import is_username_valid

from .conftest import (
    valid_usernames,
    valid_passwords,
    valid_emails,
    invalid_usernames,
    invalid_passwords,
    invalid_emails,
)

test_datas = [
    {"key_1": 1, "key_2": "some-value"},
    {"hello": {"key": "value"}, "world": -23},
    {
        "obj": {"val": 23, "other_val": {"foo": "bar"}},
        "other_obj": {"test": ["test", "list"]},
    },
]
test_time_deltas = [
    timedelta(days=1),
    timedelta(seconds=4),
    timedelta(minutes=0.8),
]
test_user_records = [
    UserSchema(username="user_1", password_hash="hash_1", email="email_1"),
    UserSchema(username="user_2", password_hash="hash_2", email="email_2"),
    UserSchema(username="user_3", password_hash="hash_3", email="email_3"),
]


class TestCreateAccessToken:
    @freeze_time("2022-11-06")
    @pytest.mark.parametrize("test_data", test_datas)
    def test_create_access_token(self, test_data: dict[str, Any]):
        # test WITH NO given expires_delta param
        copy_data = test_data.copy()

        # create token
        access_token = create_access_token(test_data)

        # decode token
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])

        # payload should have an exp property added to the original test_data
        expected_expire = int(
            (datetime.utcnow() + timedelta(minutes=15)).timestamp()
        )
        copy_data.update({"exp": expected_expire})

        assert payload == copy_data

        with pytest.raises(JWTError):
            jwt.decode(
                access_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM]
            )

    @freeze_time("2022-11-06")
    @pytest.mark.parametrize(
        "test_data,test_time_delta", zip(test_datas, test_time_deltas)
    )
    def test_create_access_token_with_time_delta(
        self, test_data: dict[str, Any], test_time_delta: timedelta
    ):

        # test WITH a given expires_delta param
        copy_data = test_data.copy()

        access_token = create_access_token(test_data, test_time_delta)

        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])

        # payload should have an exp property added to the original test_data
        expected_expire = int((datetime.utcnow() + test_time_delta).timestamp())
        copy_data.update({"exp": expected_expire})

        assert payload == copy_data

        with pytest.raises(JWTError):
            jwt.decode(
                access_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM]
            )

    def test_create_access_token_expires(self):
        # set expires delta to a negative value
        access_token = create_access_token(test_datas[0], timedelta(days=-10))

        # the access token should therefore be expired
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])


@freeze_time("2022-11-06")
@pytest.mark.parametrize("test_user_record", test_user_records)
def test_create_login_token(test_user_record: UserSchema):
    # generate login token for the user
    login_token = create_login_token(test_user_record)

    # the expected expiry should use the LOGIN_TOKEN_EXPIRE_MINUTES constant
    expected_expire = int(
        (
            datetime.utcnow() + timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)
        ).timestamp()
    )

    # here we generate the expected token data
    expected_token_data = TokenData(
        user_id=test_user_record.user_id,
        username=test_user_record.username,
        email=test_user_record.email,
    ).dict()
    expected_token_data.update({"exp": expected_expire})

    # decode the payload
    payload = jwt.decode(login_token, JWT_SECRET, algorithms=[ALGORITHM])

    assert payload == expected_token_data

    with pytest.raises(JWTError):
        jwt.decode(login_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM])


class TestIsPasswordValid:
    @pytest.mark.parametrize(
        "password",
        valid_passwords,
    )
    def test_valid_password(self, password: str):
        is_valid = is_password_valid(password)
        assert is_valid is True

    @pytest.mark.parametrize(
        "password",
        invalid_passwords,
    )
    def test_invalid_password(self, password: str):
        is_valid = is_password_valid(password)
        assert is_valid is False


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


class TestIsEmailValid:
    @pytest.mark.parametrize(
        "email",
        valid_emails,
    )
    @patch("messenger.helpers.auth.is_email_valid.UserHandler.get_user")
    def test_valid_email(self, get_user_mock: MagicMock, email: str):
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
    def test_invalid_email(self, get_user_mock: MagicMock, email: str):
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
    def test_email_exists(self, get_user_mock: MagicMock, email: str):
        get_user_mock.return_value = test_user_records[0]
        validity_data = is_email_valid(MagicMock(), email)

        assert validity_data.is_valid is False
        assert validity_data.detail == EmailError.ACCOUNT_EXISTS.value
