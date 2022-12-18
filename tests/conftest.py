"""Shared data/functions used during tests"""

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import engine
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_code_schema import (
    FriendshipStatusCodeSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from tests import TestingSessionLocal

valid_passwords = [
    "Password231",
    "aValidpassword2",
    "eloWor1d",
    "2_password_D-*9)",
    ')(@#&*"@#(*@GOod22',
]

invalid_passwords = [
    "aBC4567",
    "not_upper_case2",
    "ONLY UPPER12 CASE",
    "noNumbers",
    "22123233",
]

valid_usernames = [
    "valid_username.23",
    "vAli",
    "hello.world",
    "223221",
    "USERNAME",
    "username",
    "hie",
]

invalid_usernames = [
    "_invalid",
    "invalid_",
    "invalid__user",
    "hi_.there",
    "some._user",
    "boop..bop",
    "bing...bang",
    "also__.invalid",
    "has*invalid)()@#characters",
    "this_username_is_far_too_long_to_be_valid",
    "hi",
]

valid_emails = [
    "email@email.com",
    "something@email.com",
    "my.ownsite@ourearth.org",
    "aperson@gmail.com",
]

invalid_emails = ["@email.com", "cool.cool", "not an email", "google.email@com"]

# functions to assist generation of users for tests
def generate_username(user_id: int) -> str:
    return "username" + str(user_id)


def generate_email(user_id: int) -> str:
    return "email" + str(user_id)


def get_user_schema_params(user_id: int):
    return {
        "user_id": user_id,
        "email": generate_email(user_id),
        "username": generate_username(user_id),
        "password_hash": "password",
    }


@pytest.fixture()
def session():
    """This function returns a database session where no actual
    transactions are commited to the test database. This ensures
    that no tables actually need to be created. SQLAlchemy handles
    all table relationships, etc.

    Yields:
        Session: the database session to test with
    """
    connection = engine.connect()
    transaction = connection.begin()
    db: Session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()

    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @event.listens_for(db, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield db

    # Rollback the overall transaction, restoring the state before the test ran.
    db.close()
    transaction.rollback()
    connection.close()


def add_initial_friendship_status_codes(session: Session):
    """Test helper function that adds all the expected status codes
    to the session that are existent in prod and dev.
    Args:
        session (Session): the session that will be used during testing
    """
    for status_code in FriendshipStatusCode:
        friendship_status_code = FriendshipStatusCodeSchema(
            status_code_id=status_code.value, name=status_code.name
        )
        session.add(friendship_status_code)

    session.commit()
