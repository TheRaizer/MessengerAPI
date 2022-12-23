from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.fastApi import app
from messenger.helpers.users import get_current_active_user


@pytest.fixture
def client(session: Session):
    current_active_user = UserSchema(
        user_id=1,
        username="test-username",
        email="test-email",
        password_hash="test-password-hash",
    )

    session.add(current_active_user)
    session.commit()
    session.refresh(current_active_user)

    def override_database_session():
        yield session

    def override_get_current_active_user():
        yield current_active_user

    app.dependency_overrides[
        get_current_active_user
    ] = override_get_current_active_user
    app.dependency_overrides[database_session] = override_database_session

    test_client = TestClient(app)

    yield (test_client, current_active_user)

    del app.dependency_overrides[database_session]
    del app.dependency_overrides[get_current_active_user]


FROZEN_DATE = "2022-11-07"
