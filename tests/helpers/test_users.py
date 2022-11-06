from fastapi import HTTPException
import pytest
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema

@pytest.fixture
def get_test_records() -> list[UserSchema]:
    test_users = [
        UserSchema(username="user_1", password_hash="hash_1", email="email_1"),
        UserSchema(username="user_2", password_hash="hash_2", email="email_2"),
        UserSchema(username="user_3", password_hash="hash_3", email="email_3")
    ]
    
    return test_users