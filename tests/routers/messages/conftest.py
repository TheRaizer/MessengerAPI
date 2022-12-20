from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.fastapi import app
from messenger.helpers.users import get_current_active_user


current_active_user = UserSchema(
    user_id=1,
    username="test-username",
    email="test-email",
    password_hash="test-password-hash",
)


session_mock = MagicMock()


def override_database_session():
    session_mock.reset_mock()
    return session_mock


def override_get_current_active_user():

    return current_active_user


@pytest.fixture
def client():
    app.dependency_overrides[
        get_current_active_user
    ] = override_get_current_active_user
    app.dependency_overrides[database_session] = override_database_session

    test_client = TestClient(app)

    return test_client
