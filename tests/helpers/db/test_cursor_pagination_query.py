from datetime import datetime
from typing import TypeVar, Type, Callable
import pytest
from pytest_mock import MockerFixture
from sqlalchemy import Column, Table
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.message_schema import (
    MessageSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.pagination import CursorState
from messenger.helpers.db import DatabaseHandler

T = TypeVar("T", bound=Table)


def get_user_schema_params(user_id: int):
    return {
        "user_id": user_id,
        "email": "email" + str(user_id),
        "username": "username" + str(user_id),
        "password_hash": "password",
    }


def get_message_schema_params(message_id: int):
    return {
        "message_id": message_id,
        "content": "content" + str(message_id),
        "created_date_time": datetime.now(),
    }


class TestCursorPaginationQuery:
    def add_schemas(
        self,
        table: Type[T],
        num_of_schemas: int,
        get_params: Callable[[int], dict],
        session: Session,
    ):
        for i in range(1, num_of_schemas + 1):
            kwargs = get_params(i)

            schema = table(**kwargs)
            session.add(schema)

        session.commit()

    @pytest.mark.parametrize(
        "table, unique_column, cursor, limit, records_to_create, get_table_params",
        [
            (
                UserSchema,
                UserSchema.username,
                None,
                2,
                2,
                get_user_schema_params,
            ),
            (
                MessageSchema,
                MessageSchema.message_id,
                CursorState.PREVIOUS.value
                + "___2",  # assign cursor state of prev___2 since we will attempt to query all messages with id less than 2, which will return one result
                1,
                1,
                get_message_schema_params,
            ),
            (
                UserSchema,
                UserSchema.email,
                None,
                4,
                4,
                get_user_schema_params,
            ),
        ],
    )
    def test_paginating_first_and_last_page_returns_null_cursors(
        self,
        table: Type[T],
        unique_column: Column,
        cursor: str,
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        session: Session,
    ):
        self.add_schemas(table, records_to_create, get_table_params, session)

        db_handler = DatabaseHandler(session)
        pagination_model = db_handler.cursor_pagination_query(
            table, unique_column, cursor, limit
        )

        assert pagination_model.cursor.prev_page is None
        assert pagination_model.cursor.next_page is None

    """
    cases to test for:
    CASES: 
        1. Cursor state is next and we are at the last page (last page is not first page), (next_page=None, prev_page="prev___...")
        2. Cursor state is next/prev and we at the last page (last page is first page), (next_page=None, prev_page=None)                --- DONE
        3. Cursor state is prev/next and we are at a middle page (next_page="next___...", prev_page="prev___...")
        4. Cursor state is prev/next and we are at first page (next_page="next___...", prev_page=None)
    """
