from typing import Optional, Tuple, Type, TypeVar
from fastapi import Depends, HTTPException, status

from sqlalchemy import Column, Table
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import (
    database_session,
)
from messenger.constants.pagination import (
    NEXT_PREFIX,
    PREVIOUS_PREFIX,
    CursorState,
)
from messenger.helpers.get_model_dict import get_model_dict

from messenger.models.pagination_model import CursorModel, CursorPaginationModel


T = TypeVar("T", bound=Table)


def get_pagination_filter(
    unique_column: Column, cursor_state: str, column_value: str
):
    if cursor_state == CursorState.NEXT.value:
        pagination_filter = unique_column > column_value
    elif cursor_state == CursorState.PREVIOUS.value:
        pagination_filter = unique_column < column_value
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid cursor format",
        )

    return pagination_filter


def cursor_parser(
    cursor: Optional[str] = None,
) -> Tuple[str, str]:
    if cursor is None:
        cursor_state = CursorState.NEXT.value
        column_value = ""
    else:
        cursor_values = cursor.split("___")

        cursor_state = cursor_values[0]
        column_value = cursor_values[1]

    return cursor_state, column_value


def cursor_pagination(
    limit: int,
    parsed_cursor: Tuple[str, str] = Depends(cursor_parser),
    db: Session = Depends(database_session),
):
    """Paginates a database query using cursors.
    If the returned model has a next_page value of None, this means
    there is no next page to paginate.

    If the returned model has a prev_page value of None, this means
    there is no previous page to paginate.

    Otherwise the client can pass the next_page and previous_page as the cursor,
    into this method with the same table and unique column, to continue paginating.

    Preconditions:
        - limit must be > 0
        - cursor must be prefixed with either next___ or prev___ or be None
        - unique_column must be a column in the given table, whose
        values are unique to each row.

    Args:
        table (Type[T]): the table (which can be a subquery) to paginate data from.
        unique_column (Column): the unique column in the given table.
        cursor (str): the cursor to tell us where to start page from.
        limit (int): the number of records to retrieve per page.

    Returns:
        CursorPaginationModel: the pagination model that contains the next and
        previous cursors, which allow further pagination requests. As well as
        the current results from this pagination.
    """
    cursor_state, column_value = parsed_cursor

    def pagination(
        table: Type[T],
        unique_column: Column,
    ) -> CursorPaginationModel:
        pagination_filter = get_pagination_filter(
            unique_column, cursor_state, column_value
        )

        page_results = (
            db.query(table)
            .filter(pagination_filter)
            .order_by(unique_column)
            .limit(limit + 1)
            .all()
        )

        if len(page_results) == 0:
            return CursorPaginationModel(
                cursor=CursorModel(prev_page=None, next_page=None),
                results=page_results,
            )

        prev_page = None
        next_page = None

        if len(page_results) < limit + 1:
            if cursor_state == CursorState.NEXT.value and column_value != "":
                # we are at last page attempting to move forwards,
                # but there is no more pages in that direction
                # last page is not first page
                prev_page = PREVIOUS_PREFIX + str(
                    get_model_dict(page_results[0])[unique_column.key]
                )
        else:
            # we cannot be at the last page, because the only case where
            # this is true is if cursor state is previous and we are at last page,
            # however this is impossible since for that to happen the given
            # cursor column value must be a value that does not exist in the database.
            # Thus we are at a middle page or first page
            if cursor_state == CursorState.NEXT.value:
                # if we are at next state then there is an additional element at the
                # end of the array due to limit + 1, which we must ignore
                next_page = NEXT_PREFIX + str(
                    get_model_dict(page_results[:-1][-1])[unique_column.key]
                )
                # if we are not first page then set prev_page
                if column_value != "":
                    prev_page = PREVIOUS_PREFIX + str(
                        get_model_dict(page_results[0])[unique_column.key]
                    )
            elif cursor_state == CursorState.PREVIOUS.value:
                # if we are at prev state then there is an additional element at the
                # start of the array due to limit + 1, which we must ignore
                next_page = NEXT_PREFIX + str(
                    get_model_dict(page_results[-1])[unique_column.key]
                )
                # we can index at 1 since we know that if limit > 0 and
                # len(page_results) > limit + 1 then len(page_results) > 1
                prev_page = PREVIOUS_PREFIX + str(
                    get_model_dict(page_results[1])[unique_column.key]
                )

        returned_results = []
        if cursor_state == CursorState.NEXT.value:
            returned_results = page_results[:-1]
        elif cursor_state == CursorState.PREVIOUS.value:
            returned_results = page_results[1:]

        return CursorPaginationModel(
            cursor=CursorModel(prev_page=prev_page, next_page=next_page),
            results=page_results
            if len(page_results) <= limit
            else returned_results,
        )

    return pagination
