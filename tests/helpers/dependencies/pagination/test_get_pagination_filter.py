from typing import Tuple
from fastapi import HTTPException
import pytest
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.helpers.dependencies.pagination import get_pagination_filter
from tests.helpers.dependencies.pagination.conftest import (
    incorrect_parsed_cursors,
)


class TestGetPaginationFilter:
    @pytest.mark.parametrize("invalid_parsed_cursor", incorrect_parsed_cursors)
    def test_raises_when_cursor_state_invalid(
        self, invalid_parsed_cursor: Tuple[str, str]
    ):
        cursor_state, column_value = invalid_parsed_cursor
        with pytest.raises(HTTPException) as exc:
            get_pagination_filter(
                True, UserSchema.username, cursor_state, column_value, ""
            )
            assert exc.value.status_code == 400
            assert exc.value.detail == "invalid cursor"
