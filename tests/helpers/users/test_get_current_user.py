from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import pytest
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth.auth_token import TokenData

from messenger.helpers.users import get_current_user
from tests.helpers.conftest import (
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
    @patch("messenger.helpers.users.validate_access_token")
    def test_when_successfully_retrieved_user(
        self,
        validate_access_token_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        username: str,
        email: str,
        token: str,
    ):
        expected_user = UserSchema()
        session_mock = mocker.MagicMock()
        validate_access_token_mock.return_value = TokenData(
            user_id="1", username=username, email=email
        )
        UserHandlerMock.return_value.get_user.return_value = expected_user
        
        user = get_current_user(session_mock, token)

        validate_access_token_mock.assert_called_once_with(token, JWT_SECRET)
        assert user is expected_user

    @pytest.mark.parametrize(
        "token",
        valid_passwords,
    )
    @patch("messenger.helpers.users.validate_access_token")
    def test_raises_when_no_valid_token_was_found(
        self,
        validate_access_token_mock: MagicMock,
        mocker: MockerFixture,
        token: str,
    ):
        validate_access_token_mock.return_value = None
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
    @patch("messenger.helpers.users.validate_access_token")
    def test_raises_when_no_user_found(
        self,
        validate_access_token_mock: MagicMock,
        UserHandlerMock: MagicMock,
        mocker: MockerFixture,
        username: str,
        email: str,
        token: str,
    ):
        validate_access_token_mock.return_value = TokenData(
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
