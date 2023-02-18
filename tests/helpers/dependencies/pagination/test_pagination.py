from typing import List, Optional, Tuple, Type, Callable
from fastapi import HTTPException
import pytest
from sqlalchemy import Column
from sqlalchemy.orm import Session
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.pagination import CursorState
from messenger.constants.generics import T
from messenger.helpers.dependencies.pagination import cursor_pagination
from tests.helpers.dependencies.pagination.conftest import (
    null_cursors_test_params,
    paginate_next_when_last_page_test_params,
    when_middle_page_test_params,
    when_first_page_test_params,
    incorrect_parsed_cursors,
    add_schemas,
)


class TestCursorPaginationQuery:
    @pytest.mark.parametrize(
        null_cursors_test_params[0],
        null_cursors_test_params[1],
    )
    def test_paginating_first_and_last_page_returns_null_cursors(
        self,
        table: Type[T],
        unique_column: Column,
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_result_ids: List[int],
        session: Session,
    ):
        expected_results = add_schemas(
            table,
            records_to_create,
            get_table_params,
            session,
            expected_result_ids,
        )

        # the only case where the client can paginate the first
        # and last page, is when given a next cursor of None
        # thus the cursor state is set to next, and value is "".
        pagination = cursor_pagination(
            limit, (CursorState.NEXT.value, ""), session
        )
        pagination_model = pagination(table, unique_column, "")

        assert pagination_model.cursor.prev_page is None
        assert pagination_model.cursor.next_page is None
        assert pagination_model.results == expected_results

    @pytest.mark.parametrize(
        paginate_next_when_last_page_test_params[0],
        paginate_next_when_last_page_test_params[1],
    )
    def test_paginating_next_when_last_page(
        self,
        table: Type[T],
        unique_column: Column,
        parsed_cursor: Tuple[str, str],
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_prev_cursor: Optional[str],
        expected_result_ids: List[int],
        session: Session,
    ):
        expected_results = add_schemas(
            table,
            records_to_create,
            get_table_params,
            session,
            expected_result_ids,
        )

        pagination = cursor_pagination(limit, parsed_cursor, session)
        pagination_model = pagination(table, unique_column, "")

        assert pagination_model.cursor.next_page is None
        assert pagination_model.cursor.prev_page == expected_prev_cursor
        assert pagination_model.results == expected_results

    @pytest.mark.parametrize(
        when_middle_page_test_params[0],
        when_middle_page_test_params[1],
    )
    def test_paginating_next_or_prev_when_middle_page(
        self,
        table: Type[T],
        unique_column: Column,
        parsed_cursor: Tuple[str, str],
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_next_cursor: Optional[str],
        expected_prev_cursor: Optional[str],
        expected_result_ids: List[int],
        session: Session,
    ):
        expected_results = add_schemas(
            table,
            records_to_create,
            get_table_params,
            session,
            expected_result_ids,
        )

        pagination = cursor_pagination(limit, parsed_cursor, session)
        pagination_model = pagination(table, unique_column, "")

        assert pagination_model.cursor.next_page == expected_next_cursor
        assert pagination_model.cursor.prev_page == expected_prev_cursor
        assert pagination_model.results == expected_results

    @pytest.mark.parametrize(
        when_first_page_test_params[0],
        when_first_page_test_params[1],
    )
    def test_paginating_next_or_prev_when_first_page(
        self,
        table: Type[T],
        unique_column: Column,
        parsed_cursor: Tuple[str, str],
        limit: int,
        records_to_create: int,
        get_table_params: Callable[[int], dict],
        expected_next_cursor: Optional[str],
        expected_result_ids: List[int],
        session: Session,
    ):
        expected_results = add_schemas(
            table,
            records_to_create,
            get_table_params,
            session,
            expected_result_ids,
        )

        pagination = cursor_pagination(limit, parsed_cursor, session)
        pagination_model = pagination(table, unique_column, "")

        assert pagination_model.cursor.next_page == expected_next_cursor
        assert pagination_model.cursor.prev_page is None

        assert pagination_model.results == expected_results

    @pytest.mark.parametrize("limit", [1, 2, 12, 52, 7, 12])
    def test_paginating_when_no_results(
        self,
        limit: int,
        session: Session,
    ):
        pagination = cursor_pagination(
            limit, (CursorState.NEXT.value, ""), session
        )
        pagination_model = pagination(UserSchema, UserSchema.username, "")

        assert pagination_model.cursor.next_page is None
        assert pagination_model.cursor.prev_page is None
        assert pagination_model.results == []

    @pytest.mark.parametrize(
        "incorrect_parsed_cursor", incorrect_parsed_cursors
    )
    def test_raises_exception_with_incorrect_cursor_format(
        self,
        incorrect_parsed_cursor: Tuple[str, str],
        session: Session,
    ):
        pagination = cursor_pagination(1, incorrect_parsed_cursor, session)

        with pytest.raises(HTTPException) as exc:
            pagination(UserSchema, UserSchema.username, "")

            assert exc.value.status_code == 400
            assert exc.value.detail == "invalid cursor"
