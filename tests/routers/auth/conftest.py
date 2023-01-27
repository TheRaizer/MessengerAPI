import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from messenger_schemas.schema import (
    database_session,
)
from messenger.fastApi import app


@pytest.fixture
def client(session: Session):
    def override_database_session():
        yield session

    app.dependency_overrides[database_session] = override_database_session

    test_client = TestClient(app)

    yield test_client

    del app.dependency_overrides[database_session]
