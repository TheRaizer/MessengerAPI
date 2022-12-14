from datetime import datetime
from typing import Callable, List, Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import Table
from _submodules.messenger_utils.messenger_schemas.schema.message_schema import (
    MessageSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.pagination import CursorState

# * Note that the ORDER BY command which is used in cursor pagination
# * will not order alphanumeric strings as expected. Mainly when entering
# * the use of double digits or more.


def generate_user_name(user_id: int) -> str:
    return "username" + str(user_id)


def generate_email(user_id: int) -> str:
    return "email" + str(user_id)


def get_user_schema_params(user_id: int):
    return {
        "user_id": user_id,
        "email": generate_email(user_id),
        "username": generate_user_name(user_id),
        "password_hash": "password",
    }


def get_message_schema_params(message_id: int):
    return {
        "message_id": message_id,
        "content": "content" + str(message_id),
        "created_date_time": datetime.now(),
    }


# Create parameters under the pretense that the unique column will
# be made from one of get_..._params functions.
# These params are passed too pytest.mark.parametrize.
next_when_last_page_test_params = (
    "table, unique_column, cursor, limit, records_to_create, get_table_params, expected_prev_cursor, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            CursorState.NEXT.value + "___" + generate_user_name(2),
            2,
            4,
            get_user_schema_params,
            CursorState.PREVIOUS.value + "___" + generate_user_name(3),
            [3, 4],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            CursorState.NEXT.value + "___2",
            1,
            3,
            get_message_schema_params,
            CursorState.PREVIOUS.value + "___3",
            [3],
        ),
        (
            UserSchema,
            UserSchema.email,
            CursorState.NEXT.value + "___" + generate_email(4),
            2,
            5,
            get_user_schema_params,
            CursorState.PREVIOUS.value + "___" + generate_email(5),
            [5, 6],
        ),
    ],
)

when_first_page_test_params = (
    "table, unique_column, limit, records_to_create, get_table_params, expected_next_cursor, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            2,
            4,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_user_name(2),
            [1, 2],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            1,
            2,
            get_message_schema_params,
            CursorState.NEXT.value + "___1",
            [1],
        ),
        (
            UserSchema,
            UserSchema.email,
            5,
            9,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_email(5),
            [1, 2, 3, 4, 5],
        ),
    ],
)


when_middle_page_test_params = (
    "table, unique_column, cursor, limit, records_to_create, get_table_params, expected_next_cursor, expected_prev_cursor, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            CursorState.NEXT.value + "___" + generate_user_name(5),
            3,
            10,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_user_name(8),
            CursorState.PREVIOUS.value + "___" + generate_user_name(6),
            [6, 7, 8],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            CursorState.PREVIOUS.value + "___4",
            2,
            5,
            get_message_schema_params,
            CursorState.NEXT.value + "___3",
            CursorState.PREVIOUS.value + "___2",
            [2, 3],
        ),
        (
            UserSchema,
            UserSchema.email,
            CursorState.NEXT.value + "___" + generate_email(3),
            5,
            14,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_email(8),
            CursorState.PREVIOUS.value + "___" + generate_email(4),
            [4, 5, 6, 7, 8],
        ),
    ],
)

null_cursors_test_params = (
    "table, unique_column, cursor, limit, records_to_create, get_table_params, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            None,
            2,
            2,
            get_user_schema_params,
            [1, 2],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            CursorState.PREVIOUS.value + "___2",
            3,
            1,
            get_message_schema_params,
            [1],
        ),
        (
            UserSchema,
            UserSchema.email,
            None,
            5,
            4,
            get_user_schema_params,
            [1, 2, 3, 4],
        ),
    ],
)


T = TypeVar("T", bound=Table)


def add_schemas(
    table: Type[T],
    num_of_schemas: int,
    get_params: Callable[[int], dict],
    session: Session,
    expected_result_ids: List[int],
) -> List[T]:
    expected_results: List[T] = []
    for i in range(1, num_of_schemas + 1):
        kwargs = get_params(i)

        schema = table(**kwargs)

        if i in expected_result_ids:
            expected_results.append(schema)

        session.add(schema)

    session.commit()

    return expected_results