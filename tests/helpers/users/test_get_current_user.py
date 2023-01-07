from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import pytest
from pytest_mock import MockerFixture
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.settings import JWT_SECRET
from messenger.helpers.tokens.auth_tokens import AccessTokenData

from messenger.helpers.users import get_current_user
from tests.conftest import (
    valid_usernames,
    valid_emails,
    valid_passwords,
)


class TestGetCurrentUser:
    @pytest.mark.parametrize(
        "username, email, token",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    @patch("messenger.helpers.users.UserHandler")
    @patch("messenger.helpers.users.validate_token")
    def test_when_successfully_retrieved_user(
        self,
        validate_token_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        username: str,
        email: str,
        token: str,
    ):
        expected_user = UserSchema()
        session_mock = mocker.MagicMock()
        validate_token_mock.return_value = AccessTokenData(
            user_id="1", username=username, email=email
        )
        UserHandlerMock.return_value.get_user.return_value = expected_user

        user = get_current_user(session_mock, token)

        validate_token_mock.assert_called_once_with(
            token, JWT_SECRET, AccessTokenData
        )
        assert user is expected_user

    @pytest.mark.parametrize(
        "token",
        valid_passwords,
    )
    @patch("messenger.helpers.users.validate_token")
    def test_raises_when_no_valid_token_was_found(
        self,
        validate_token_mock: MagicMock,
        mocker: MockerFixture,
        token: str,
    ):
        validate_token_mock.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_current_user(mocker.MagicMock(), token)

            assert exc.value.status_code == 401
            assert exc.value.detail == "Could not validate credentials"
            assert exc.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.parametrize(
        "username, email, token",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    @patch("messenger.helpers.users.UserHandler")
    @patch("messenger.helpers.users.validate_token")
    def test_raises_when_no_user_found(
        self,
        validate_token_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        username: str,
        email: str,
        token: str,
    ):
        validate_token_mock.return_value = AccessTokenData(
            user_id="1", username=username, email=email
        )
        UserHandlerMock.return_value.get_user.side_effect = HTTPException(
            status_code=404
        )

        with pytest.raises(HTTPException) as exc:
            get_current_user(mocker.MagicMock(), token)

            assert exc.value.status_code == 401
            assert exc.value.detail == "Could not validate credentials"
            assert exc.value.headers == {"WWW-Authenticate": "Bearer"}
