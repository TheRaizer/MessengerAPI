from datetime import timedelta
from messenger_schemas.schema.user_schema import (
    UserSchema,
)


test_datas = [
    {"key_1": 1, "key_2": "some-value"},
    {"hello": {"key": "value"}, "world": -23},
    {
        "obj": {"val": 23, "other_val": {"foo": "bar"}},
        "other_obj": {"test": ["test", "list"]},
    },
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
