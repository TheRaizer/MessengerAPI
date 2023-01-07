from datetime import timedelta
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from pydantic import BaseModel


class TestTokenDataModel1(BaseModel):
    user_id: int


class TestTokenDataModel2(BaseModel):
    username: str
    email: str


test_token_datas = [
    TestTokenDataModel1(user_id=12),
    TestTokenDataModel2(username="user", email="email"),
    TestTokenDataModel1(user_id=22),
]
test_time_deltas = [
    timedelta(days=1),
    timedelta(seconds=4),
    timedelta(minutes=0.8),
]
test_user_records = [
    UserSchema(username="user_1", password_hash="hash_1", email="email_1"),
    UserSchema(username="user_2", password_hash="hash_2", email="email_2"),
    UserSchema(username="user_3", password_hash="hash_3", email="email_3"),
]
