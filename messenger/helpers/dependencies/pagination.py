import logging
from typing import Optional, Tuple, Type, TypeVar
from fastapi import Depends, HTTPException, Query, status

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
logger = logging.getLogger(__name__)

INVALID_CURSOR_HTTP_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="invalid cursor",
)


def get_pagination_filter(
    unique_column: Column, cursor_state: str, column_value: str
):
    if cursor_state == CursorState.NEXT.value:
        pagination_filter = unique_column > column_value
    elif cursor_state == CursorState.PREVIOUS.value:
        pagination_filter = unique_column < column_value
    else:
        raise INVALID_CURSOR_HTTP_EXCEPTION

    return pagination_filter


def cursor_parser(
    cursor: Optional[str] = None,
) -> Tuple[str, str]:
    if cursor is None:
        cursor_state = CursorState.NEXT.value
        column_value = ""
    else:
        cursor_values = cursor.split("___")

        if len(cursor_values) != 2:
            raise INVALID_CURSOR_HTTP_EXCEPTION

        cursor_state = cursor_values[0]
        column_value = cursor_values[1]

    return cursor_state, column_value


def determine_cursor_query_order(
    unique_column: Column,
    cursor_state: str,
):
    """Change the ORDER BY in query depending on cursor state. (this ensures the limit
    is enforced on the correct side of the table, either from the start or the end)

    - If we are obtaining previous page, then we want to enforce limit starting
    at the end of the table.

    - If we are obtaining next page, then we want to enforce limit starting at
    the start of the table.

    To gain a better understanding try executing the queries in MySQL without
    clarifying desc or asc. You will notice that the returned columns when filtering
    with "<" and a set LIMIT will return records starting from the beginning of the
    queried table.

    Now try setting order by with desc. You will now see that it queries the expected, records
    albeit in reverse order.
    """
    order_by = (
        unique_column.asc()
        if cursor_state == CursorState.NEXT.value
        else unique_column.desc()
    )

    return order_by


def cursor_pagination(
    limit: int = Query(
        title="The limit on the number of items to paginate", gt=0
    ),
    parsed_cursor: Tuple[str, str] = Depends(cursor_parser),
    db: Session = Depends(database_session),
):
    """Produces a function that executes cursor pagination on a
    database query.

    Preconditions:
        - limit must be > 0
        - cursor must be prefixed with either next___ or prev___ or be None

    Args:
        parsed_cursor (str): the parsed_cursor that contains a cursor_state and column_value.
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
        """Paginates a database query using cursors.

        - If the returned model has a next_page value of None, this means
        there is no next page to paginate.

        - If the returned model has a prev_page value of None, this means
        there is no previous page to paginate.

        Otherwise the client can pass the next_page and previous_page as the cursor,
        into this method with the same table and unique column, to continue paginating.

        Preconditions:
            - unique_column must be a column in the given table, whose
            values are unique to each row.

        Args:
            table (Type[T]): the table (which can be a subquery) to paginate data from.
            unique_column (Column): the unique column in the given table.

        Returns:
            CursorPaginationModel: the pagination model that contains the next and
            previous cursors, which allow further pagination requests. As well as
            the current results from this pagination.
        """

        pagination_filter = get_pagination_filter(
            unique_column, cursor_state, column_value
        )
        order_by = determine_cursor_query_order(unique_column, cursor_state)

        page_results = (
            db.query(table)
            .filter(pagination_filter)
            .order_by(order_by)
            .limit(limit + 1)
            .all()
        )

        if len(page_results) == 0:
            return CursorPaginationModel(
                cursor=CursorModel(prev_page=None, next_page=None),
                results=page_results,
            )

        # if its previous, then we ordered by desc, thus we need to reverse
        # the array to get the correct order.
        if cursor_state == CursorState.PREVIOUS.value:
            page_results = page_results[::-1]

        prev_page = None
        next_page = None

        returned_results = []

        if len(page_results) < limit + 1:
            # We are either at the first or last page, depending on cursor_state.

            if cursor_state == CursorState.NEXT.value and column_value != "":
                """We are at last page attempting to move forwards,
                but there is no more pages in that direction
                and last page is not first page, thus previous page exists
                and next page does not.
                """
                prev_page = PREVIOUS_PREFIX + str(
                    get_model_dict(page_results[0])[unique_column.key]
                )
            elif cursor_state == CursorState.PREVIOUS.value:
                """We are at the first page, attempting to move backwards.
                When cursoring previous, we can never be at the first
                and last page at the same time. Since that would require
                that the cursor value is one in front of the last database record
                which is impossible. Thus a next page must exist. And previous page
                does not.
                """
                next_page = NEXT_PREFIX + str(
                    get_model_dict(page_results[-1])[unique_column.key]
                )
        else:
            # We are at a middle page or --if cursor == None and
            # cursor_state is next, then-- first page
            if cursor_state == CursorState.NEXT.value:
                next_page = NEXT_PREFIX + str(
                    get_model_dict(page_results[:-1][-1])[unique_column.key]
                )
                # if we are not first page then set prev_page
                if column_value != "":
                    prev_page = PREVIOUS_PREFIX + str(
                        get_model_dict(page_results[0])[unique_column.key]
                    )

                # if we are at next state then there is an additional element at the
                # end of the array due to limit + 1, which we must ignore
                returned_results = page_results[:-1]
            elif cursor_state == CursorState.PREVIOUS.value:
                next_page = NEXT_PREFIX + str(
                    get_model_dict(page_results[-1])[unique_column.key]
                )
                # we can index at 1 since we know that if limit > 0 and
                # len(page_results) > limit + 1 then len(page_results) > 1
                prev_page = PREVIOUS_PREFIX + str(
                    get_model_dict(page_results[1])[unique_column.key]
                )

                # if we are at prev state then there is an additional element at the
                # start of the array due to limit + 1, which we must ignore
                returned_results = page_results[1:]

        return CursorPaginationModel(
            cursor=CursorModel(prev_page=prev_page, next_page=next_page),
            results=page_results
            if len(page_results) <= limit
            else returned_results,
        )

    return pagination
