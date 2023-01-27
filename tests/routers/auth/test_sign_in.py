from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
import pytest
from tests.conftest import (
    valid_emails,
    valid_passwords,
)


class TestSignIn:
    @patch("messenger.helpers.auth.user.password_hasher")
    @pytest.mark.parametrize(
        "email, password",
        zip(valid_emails, valid_passwords),
    )
    def test_returns_201_on_success(
        self,
        password_hasher_mock: MagicMock,
        email: str,
        password: str,
        client: TestClient,
        session: Session,
    ):
        password_hasher_mock.verify.return_value = True

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        session.add(
            UserSchema(
                username="some_username",
                email=email,
                password_hash=password,
            )
        )
        session.commit()

        response = client.post("/auth/sign-in", body)

        assert response.status_code == 201

    @patch("messenger.helpers.auth.user.password_hasher")
    @patch("messenger.routers.auth.create_login_token")
    @pytest.mark.parametrize(
        "email, password",
        zip(valid_emails, valid_passwords),
    )
    def test_returns_access_token_on_success(
        self,
        create_login_token_mock: MagicMock,
        password_hasher_mock: MagicMock,
        email: str,
        password: str,
        client: TestClient,
        session: Session,
    ):
        password_hasher_mock.verify.return_value = True

        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        session.add(
            UserSchema(
                username="some_username",
                email=email,
                password_hash=password,
            )
        )
        session.commit()
        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        create_login_token_mock.return_value = "access_token_mock"

        response = client.post("/auth/sign-in", body)

        assert response.status_code == 201
        assert response.json() == {
            "access_token": "access_token_mock",
            "token_type": "bearer",
        }

    @pytest.mark.parametrize(
        "email, password",
        zip(valid_emails, valid_passwords),
    )
    def test_sign_in_produces_404_when_no_user_found(
        self,
        email: str,
        password: str,
        client: TestClient,
    ):
        body = {
            "grant_type": "password",
            "username": email,
            "password": password,
        }

        response = client.post("/auth/sign-in", body)

        assert response.status_code == 404
        assert response.json() == {"detail": "no such user exists"}

    @pytest.mark.parametrize(
        "email, password",
        zip(valid_emails, valid_passwords),
    )
    def test_sign_in_produces_401_when_credentials_invalid(
        self,
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
                username="some_username",
                email=email,
                password_hash=password,
            )
        )
        session.commit()

        response = client.post("/auth/sign-in", body)

        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}
