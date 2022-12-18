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
from tests.conftest import (
    generate_email,
    generate_username,
    get_user_schema_params,
)

# * Note that the ORDER BY command which is used in cursor pagination
# * will not order alphanumeric strings as expected. Mainly when entering
# * the use of double digits or more.


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
    "table, unique_column, parsed_cursor, limit, records_to_create, get_table_params, expected_prev_cursor, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            (CursorState.NEXT.value, generate_username(2)),
            2,
            4,
            get_user_schema_params,
            CursorState.PREVIOUS.value + "___" + generate_username(3),
            [3, 4],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            (CursorState.NEXT.value, "2"),
            1,
            3,
            get_message_schema_params,
            CursorState.PREVIOUS.value + "___3",
            [3],
        ),
        (
            UserSchema,
            UserSchema.email,
            (CursorState.NEXT.value, generate_email(4)),
            2,
            5,
            get_user_schema_params,
            CursorState.PREVIOUS.value + "___" + generate_email(5),
            [5, 6],
        ),
    ],
)

when_first_page_test_params = (
    "table, unique_column, parsed_cursor, limit, records_to_create, get_table_params, expected_next_cursor, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            (CursorState.NEXT.value, ""),
            2,
            4,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_username(2),
            [1, 2],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            (CursorState.PREVIOUS.value, "2"),
            1,
            4,
            get_message_schema_params,
            CursorState.NEXT.value + "___1",
            [1],
        ),
        (
            UserSchema,
            UserSchema.email,
            (CursorState.NEXT.value, ""),
            5,
            9,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_email(5),
            [1, 2, 3, 4, 5],
        ),
        (
            UserSchema,
            UserSchema.username,
            (CursorState.NEXT.value, ""),
            3,
            3,
            get_user_schema_params,
            None,
            [1, 2, 3],
        ),
        (
            UserSchema,
            UserSchema.email,
            (CursorState.PREVIOUS.value, generate_email(4)),
            5,
            9,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_email(3),
            [1, 2, 3],
        ),
        (
            UserSchema,
            UserSchema.email,
            (CursorState.PREVIOUS.value, generate_email(6)),
            5,
            9,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_email(5),
            [1, 2, 3, 4, 5],
        ),
    ],
)


when_middle_page_test_params = (
    "table, unique_column, parsed_cursor, limit, records_to_create, get_table_params, expected_next_cursor, expected_prev_cursor, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            (CursorState.NEXT.value, generate_username(5)),
            3,
            10,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_username(8),
            CursorState.PREVIOUS.value + "___" + generate_username(6),
            [6, 7, 8],
        ),
        (
            MessageSchema,
            MessageSchema.message_id,
            (CursorState.PREVIOUS.value, "4"),
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
            (CursorState.NEXT.value, generate_email(3)),
            5,
            14,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_email(8),
            CursorState.PREVIOUS.value + "___" + generate_email(4),
            [4, 5, 6, 7, 8],
        ),
        (
            UserSchema,
            UserSchema.username,
            (CursorState.PREVIOUS.value, generate_username(6)),
            3,
            7,
            get_user_schema_params,
            CursorState.NEXT.value + "___" + generate_username(5),
            CursorState.PREVIOUS.value + "___" + generate_username(3),
            [3, 4, 5],
        ),
    ],
)

null_cursors_test_params = (
    "table, unique_column, limit, records_to_create, get_table_params, expected_result_ids",
    [
        (
            UserSchema,
            UserSchema.username,
            2,
            2,
            get_user_schema_params,
            [1, 2],
        ),
        # ( #* This is a great example of a situation that cannot occur.
        # *Since the client would never recieve a cursor state where the cursor value
        # *of "2" is given, since a column with value "2" is not in the database.
        #     MessageSchema,
        #     MessageSchema.message_id,
        #     (
        #         CursorState.PREVIOUS.value,
        #         "2",
        #     ),
        #     3,
        #     1,
        #     get_message_schema_params,
        #     [1],
        # ),
        (
            MessageSchema,
            MessageSchema.message_id,
            3,
            1,
            get_message_schema_params,
            [1],
        ),
        (
            UserSchema,
            UserSchema.email,
            5,
            4,
            get_user_schema_params,
            [1, 2, 3, 4],
        ),
    ],
)

incorrect_parsed_cursors = [
    ("awds", ""),
    ("incorrect", "values"),
    ("___", "username"),
    ("", ""),
]

invalid_cursors = ["incorrect", "not__valid", "hu_oh", "ping pong", ""]
valid_cursor_params = [
    (
        CursorState.NEXT.value + "___username23",
        (CursorState.NEXT.value, "username23"),
    ),
    (
        CursorState.PREVIOUS.value + "___somecolumnvalue",
        (CursorState.PREVIOUS.value, "somecolumnvalue"),
    ),
    (
        CursorState.NEXT.value + "___a_valid_value",
        (CursorState.NEXT.value, "a_valid_value"),
    ),
]

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
