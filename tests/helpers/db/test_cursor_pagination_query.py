from typing import Optional, Type, Callable, TypeVar
import pytest
from sqlalchemy import Column, Table
from sqlalchemy.orm import Session
from messenger.helpers.db import DatabaseHandler
from tests.helpers.db.conftest import (
    null_cursors_test_params,
    next_when_last_page_test_params,
    when_middle_page_test_params,
    when_first_page_test_params,
    add_schemas,
)

T = TypeVar("T", bound=Table)


class TestCursorPaginationQuery:
    """
    Possible cases:
        1. Cursor state is next and we are at the last page (last page is not first page), (next_page=None, prev_page="prev___...")
        2. Cursor state is next/prev and we at the last page (last page is first page), (next_page=None, prev_page=None)
        3. Cursor state is prev/next and we are at a middle page (next_page="next___...", prev_page="prev___...")
        4. Cursor state is prev/next and we are at first page (next_page="next___...", prev_page=None)
    """

    @pytest.mark.parametrize(
        null_cursors_test_params[0],
        null_cursors_test_params[1],
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
        add_schemas(table, records_to_create, get_table_params, session)

        db_handler = DatabaseHandler(session)
        pagination_model = db_handler.cursor_pagination_query(
            table, unique_column, cursor, limit
        )

        assert pagination_model.cursor.prev_page is None
        assert pagination_model.cursor.next_page is None

    @pytest.mark.parametrize(
        next_when_last_page_test_params[0],
        next_when_last_page_test_params[1],
    )
    def test_paginating_next_cursor_when_last_page(
        self,
        table: Type[T],
        unique_column: Column,
        cursor: str,
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_prev_cursor: Optional[str],
        session: Session,
    ):
        add_schemas(table, records_to_create, get_table_params, session)

        db_handler = DatabaseHandler(session)
        pagination_model = db_handler.cursor_pagination_query(
            table, unique_column, cursor, limit
        )

        assert pagination_model.cursor.next_page is None
        assert pagination_model.cursor.prev_page == expected_prev_cursor

    @pytest.mark.parametrize(
        when_middle_page_test_params[0],
        when_middle_page_test_params[1],
    )
    def test_paginating_next_or_prev_cursor_when_middle_page(
        self,
        table: Type[T],
        unique_column: Column,
        cursor: str,
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_next_cursor: Optional[str],
        expected_prev_cursor: Optional[str],
        session: Session,
    ):
        add_schemas(table, records_to_create, get_table_params, session)

        db_handler = DatabaseHandler(session)
        pagination_model = db_handler.cursor_pagination_query(
            table, unique_column, cursor, limit
        )

        assert pagination_model.cursor.next_page == expected_next_cursor
        assert pagination_model.cursor.prev_page == expected_prev_cursor

    @pytest.mark.parametrize(
        when_first_page_test_params[0],
        when_first_page_test_params[1],
    )
    def test_paginating_next_or_prev_cursor_when_first_page(
        self,
        table: Type[T],
        unique_column: Column,
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_next_cursor: Optional[str],
        session: Session,
    ):
        add_schemas(table, records_to_create, get_table_params, session)

        db_handler = DatabaseHandler(session)
        pagination_model = db_handler.cursor_pagination_query(
            table, unique_column, None, limit
        )

        assert pagination_model.cursor.next_page == expected_next_cursor
        assert pagination_model.cursor.prev_page is None

    """
    cases to test for:
    CASES: 
        1. Cursor state is next and we are at the last page (last page is not first page), (next_page=None, prev_page="prev___...")     --- DONE
        2. Cursor state is next/prev and we at the last page (last page is first page), (next_page=None, prev_page=None)                --- DONE
        3. Cursor state is prev/next and we are at a middle page (next_page="next___...", prev_page="prev___...")                       --- DONE
        4. Cursor state is prev/next and we are at first page (next_page="next___...", prev_page=None)                                  --- DONE
    """
