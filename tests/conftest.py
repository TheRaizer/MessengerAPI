import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_code_schema import FriendshipStatusCodeSchema
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.fastApi import app
from fastapi.testclient import TestClient
from _submodules.messenger_utils.messenger_schemas.schema import Base, database_session
from _submodules.messenger_utils.messenger_schemas.schema import engine

TestingSessionLocal: Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

@pytest.fixture()
def session():
    """This function returns a database session where no actual transactions are commited to the test database.
    This ensures that no tables actually need to be created. SQLAlchemy handles all table relationships, etc. 

    Yields:
        Session: the database session to test with
    """
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


def add_initial_friendship_status_codes(session: Session):
    """Test helper function that adds all the expected status codes to the session that are existent in prod and dev.

    Args:
        session (Session): the session that will be used during testing
    """
    for status_code in FriendshipStatusCode:
        friendship_status_code = FriendshipStatusCodeSchema(status_code_id=status_code.value, name=status_code.name)
        session.add(friendship_status_code)
    
    session.commit()
