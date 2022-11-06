import pytest
from sqlalchemy import create_engine
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_code_schema import FriendshipStatusCodeSchema
from messenger.fastApi import app
from fastapi.testclient import TestClient
from _submodules.messenger_utils.messenger_schemas.schema import Base, database_session
from _submodules.messenger_utils.messenger_schemas.schema import engine

TestingSessionLocal: Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

@pytest.fixture()
def session():
    connection = engine.connect()
    transaction = connection.begin()
    session: Session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()

    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @sa.event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()
    
    yield session

    # Rollback the overall transaction, restoring the state before the test ran.
    session.close()
    transaction.rollback()
    connection.close()
    
@pytest.fixture()
def client(session):
    def override_database_session():
        yield session

    app.dependency_overrides[database_session] = override_database_session
    yield TestClient(app)
    del app.dependency_overrides[database_session]