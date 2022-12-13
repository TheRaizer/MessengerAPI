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
from messenger.constants.pagination import CursorState

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
        cursor: str,
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
        cursor_values = cursor.split("___")

        cursor_state = cursor_values[0]
        column_value = cursor_values[1]

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

        previous_page_value = (
            ""
            if len(page_results) == 0
            else str(dict(page_results[0])[unique_column.key])
        )

        prev_page = (
            previous_prefix
            if cursor == ""
            else previous_prefix + previous_page_value
        )

        next_page = (
            next_prefix
            if len(page_results) < limit + 1
            else next_prefix + str(dict(page_results[-1])[unique_column.key])
        )

        return CursorPaginationModel(
            cursor=CursorModel(prev_page=prev_page, next_page=next_page),
            results=page_results
            if len(page_results) <= limit
            else page_results[:-1],
        )
