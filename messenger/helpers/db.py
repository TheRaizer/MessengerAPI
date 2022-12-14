from typing import (
    List,
    Optional,
    Type,
    TypeVar,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import Column, Table
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import (
    NoResultFound,
)
from sqlalchemy.exc import (
    MultipleResultsFound,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.pagination import CursorState
from messenger.helpers.get_model_dict import get_model_dict

from messenger.models.pagination_model import CursorModel, CursorPaginationModel

T = TypeVar("T", bound=Table)


class DatabaseHandler:
    """Handles basic database functionality."""

    def __init__(self, db: Session):
        self._db = db

    def _get_record(self, Schema: T, *criterion) -> Optional[T]:
        """Retrieves a single record from a database that matches a set of filters.
        If multiple are found we throw an HTTP 500 internal server error.
        If no result is found return None.

        Args:
            Schema (Base): the SQLAlchemy schema that relates to the table
                in the database the row will be retrieved from.
            criterion (optional): additional keyword arguments that
                will be used as filters in the query.

        Raises:
            HTTP_500_INTERNAL_SERVER_ERROR: this is raised when multiple records are returned

        Returns:
            Base: returns a database record.
        """
        try:
            db_record: Optional[T] = (
                self._db.query(Schema).filter(*criterion).one()
            )
        except MultipleResultsFound as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Multiple records found",
            ) from exc
        except NoResultFound:
            return None

        return db_record

    def _get_records(self, Schema: Type[T], *criterion) -> Optional[List[T]]:
        """Retrieve a list of records from a database.

        Args:
            Schema (T): the schema type to retrieve.
            criterion (optional): additional keyword arguments that will
                be used as filters in the query.

        Returns:
            Optional[List[T]]: a list of the given schema type records
            or None if no records were found.
        """
        db_records: List[T] = list(self._db.query(Schema).filter(*criterion))

        if len(db_records) == 0:
            return None

        return db_records

    def _get_record_with_not_found_raise(
        self, Schema: T, detail: str, *criterion
    ) -> T:
        """Retrieves the a single record from a database that matches a set of filters.

        Args:
            Schema (Base): the SQLAlchemy schema that relates to the
                table in the database the row will be retrieved from.
            criterion (optional): additional keyword arguments that will
                be used as filters in the query.

        Raises:
            HTTP_404_NOT_FOUND: this is raised when no record is found
            HTTP_500_INTERNAL_SERVER_ERROR: this is raised when multiple records are returned

        Returns:
            Base: returns a database record.
        """
        db_record = self._get_record(Schema, *criterion)

        if db_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        return db_record

    def cursor_pagination_query(
        self,
        table: Type[T],
        unique_column: Column,
        cursor: Optional[str],
        limit: int,
    ) -> CursorPaginationModel:
        """Paginates a database query using cursors.
        If the returned model has a next_page value of next___, this means
        there is no next page to paginate.

        If the returned model has a prev_page value of prev___, this means
        there is no previous page to paginate.

        Otherwise the client can pass the next_page and previous_page as the cursor,
        into this method with the same table and unique column, to continue paginating.

        Preconditions:
            - limit must be > 0
            - cursor must be prefixed with either next___ or prev___
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
        if cursor is None:
            cursor_state = CursorState.NEXT.value
            column_value = ""
        else:
            cursor_values = cursor.split("___")

            cursor_state = cursor_values[0]
            column_value = cursor_values[1]

        prev_page = None
        next_page = None

        if cursor_state == CursorState.NEXT.value:
            pagination_filter = unique_column > column_value
        else:
            pagination_filter = unique_column < column_value

        page_results = (
            self._db.query(table)
            .filter(pagination_filter)
            .order_by(unique_column)
            .limit(limit + 1)
            .all()
        )

        previous_prefix = CursorState.PREVIOUS.value + "___"
        next_prefix = CursorState.NEXT.value + "___"

        """
        CASES: 
        1. Cursor state is next and we are at the last page (last page is not first page), (next_page=None, prev_page="prev___...")
        2. Cursor state is next/prev and we at the last page (last page is first page), (next_page=None, prev_page=None)
        3. Cursor state is prev/next and we are at a middle page (next_page="next___...", prev_page="prev___...")
        4. Cursor state is prev/next and we are at first page (next_page="next___...", prev_page=None)
        
        you can tell whether you are at the first page or last page using the cursor state combined with whether the
        len(page_results) is < limit + 1
        
        you can tell whether you are at the first page when using a CursorState.NEXT when the cursor == "".
        you can tell whether you are at the first page when using CursorState.PREVIOUS when len(page_results) < limit
        """

        if len(page_results) == 0:
            return CursorPaginationModel(
                cursor=CursorModel(prev_page=None, next_page=None),
                results=page_results,
            )

        if len(page_results) < limit + 1:
            # we are either at first or last page or both depending on cursor_state

            if cursor_state == CursorState.PREVIOUS.value:
                # we are at the first page attempting to move backwards, but there is no more pages in that direction
                prev_page = None

                if len(page_results) < limit:
                    # we are on the first and last page
                    next_page = None
            elif cursor_state == CursorState.NEXT.value:
                # we are at last page attempting to move forwards, but there is no more pages in that direction
                next_page = None
                if cursor is not None:
                    # last page is not first page
                    prev_page = previous_prefix + str(
                        get_model_dict(page_results[0])[unique_column.key]
                    )
                else:
                    prev_page = None
        else:
            # we cannot be at the last page, because the only case where this is true is if cursor state is previous and we are at last page,
            # however this is impossible since for that to happen the given cursor column value must be a value that does not exist in the database.
            # Thus we are at a middle page or first page
            if cursor_state == CursorState.NEXT.value:
                # if we are at next state then there is an additional element at the end of the array due to limit + 1, which we must ignore
                next_page = next_prefix + str(
                    get_model_dict(page_results[:-1][-1])[unique_column.key]
                )
                # if we are not first page then set prev_page
                if cursor is not None:
                    prev_page = previous_prefix + str(
                        get_model_dict(page_results[0])[unique_column.key]
                    )
            elif cursor_state == CursorState.PREVIOUS.value:
                # if we are at prev state then there is an additional element at the start of the array due to limit + 1, which we must ignore
                next_page = next_prefix + str(
                    get_model_dict(page_results[-1])[unique_column.key]
                )
                # we can index at 1 since we know that if limit > 0 and len(page_results) > limit + 1 then len(page_results) > 1
                prev_page = previous_prefix + str(
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
