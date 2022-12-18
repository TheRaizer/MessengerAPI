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
from sqlalchemy import Table
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import (
    NoResultFound,
)
from sqlalchemy.exc import (
    MultipleResultsFound,
)


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
