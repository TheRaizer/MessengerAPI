from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
import pytest
from tests.conftest import (
    invalid_emails,
    invalid_usernames,
    invalid_passwords,
    valid_usernames,
    valid_emails,
    valid_passwords,
)


class TestSignUp:
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_returns_201_on_success(
        self,
        username: str,
        email: str,
        password: str,
        client: TestClient,
    ):

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        response = client.post(f"/auth/sign-up?username={username}", body)

        assert response.status_code == 201

    @patch("messenger.routers.auth.create_login_token")
    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_returns_access_token_on_success(
        self,
        create_login_token_mock: MagicMock,
        username: str,
        email: str,
        password: str,
        client: TestClient,
    ):

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        create_login_token_mock.return_value = "access_token_mock"

        response = client.post(f"/auth/sign-up?username={username}", body)

        assert response.status_code == 201
        assert response.json() == {
            "access_token": "access_token_mock",
            "token_type": "bearer",
        }

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_account_exists_has_400(
        self,
        username: str,
        email: str,
        password: str,
        client: TestClient,
        session: Session,
    ):

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        session.add(
            UserSchema(
                username=username,
                email=email,
                password_hash=password,
            )
        )
        session.commit()

        response = client.post(f"/auth/sign-up?username={username}", body)

        assert response.status_code == 400
        assert response.json() == {"detail": "account already exists"}

    @pytest.mark.parametrize(
        "invalid_username, email, password",
        zip(invalid_usernames, valid_emails, valid_passwords),
    )
    def test_invalid_username_produces_400(
        self,
        invalid_username: str,
        email: str,
        password: str,
        client: TestClient,
    ):

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        response = client.post(
            f"/auth/sign-up?username={invalid_username}", body
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "invalid username"}

    @pytest.mark.parametrize(
        "username, invalid_email, password",
        zip(valid_usernames, invalid_emails, valid_passwords),
    )
    def test_invalid_email_produces_400(
        self,
        username: str,
        invalid_email: str,
        password: str,
        client: TestClient,
    ):

        body = {
            "grant_type": "password",
            "username": invalid_email,
            "password": password,
        }

        response = client.post(f"/auth/sign-up?username={username}", body)

        assert response.status_code == 400
        assert response.json() == {"detail": "invalid email"}

    @pytest.mark.parametrize(
        "username, email, invalid_password",
        zip(valid_usernames, valid_emails, invalid_passwords),
    )
    def test_invalid_password_produces_400(
        self,
        username: str,
        email: str,
        invalid_password: str,
        client: TestClient,
    ):

        body = {
            "grant_type": "password",
            "username": email,
            "password": invalid_password,
        }

        response = client.post(f"/auth/sign-up?username={username}", body)

        assert response.status_code == 400
        assert response.json() == {"detail": "invalid password"}

    @pytest.mark.parametrize(
        "username, email, password",
        zip(valid_usernames, valid_emails, valid_passwords),
    )
    def test_when_account_username_is_taken_produces_400(
        self,
        username: str,
        email: str,
        password: str,
        client: TestClient,
        session: Session,
    ):

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        session.add(
            UserSchema(
                username=username,
                email=email + "different",
                password_hash=password,
            )
        )
        session.commit()

        response = client.post(f"/auth/sign-up?username={username}", body)

        assert response.status_code == 400
        assert response.json() == {"detail": "username is taken"}
