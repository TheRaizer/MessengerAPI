from typing import Tuple
from fastapi import HTTPException
import pytest
from messenger.constants.pagination import CursorState
from messenger.helpers.dependencies.pagination import cursor_parser
from tests.helpers.dependencies.pagination.conftest import (
    invalid_cursors,
    valid_cursor_params,
)


class TestCursorParser:
    def test_when_cursor_is_none(self):
        cursor_state, column_value = cursor_parser()

        assert cursor_state == CursorState.NEXT.value
        assert column_value == ""

    @pytest.mark.parametrize("invalid_cursor", invalid_cursors)
    def test_when_cursor_is_invalid(self, invalid_cursor: str):
        with pytest.raises(HTTPException) as exc:
            cursor_parser(invalid_cursor)
            assert exc.value.status_code == 400
            assert exc.value.detail == "invalid cursor"

    @pytest.mark.parametrize(
        "valid_cursor, expected_parsed_cursor", valid_cursor_params
    )
    def test_parses_valid_cursor_correctly(
        self, valid_cursor: str, expected_parsed_cursor: Tuple[str, str]
    ):
        parsed_cursor = cursor_parser(valid_cursor)

        assert parsed_cursor == expected_parsed_cursor
