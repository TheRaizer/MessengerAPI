from typing import List, Optional, Union, TypeVar
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

T = TypeVar('T')

def get_record(db: Session, Schema: T, *criterion) -> Optional[T]:
    """Retrieves a single record from a database that matches a set of filters.
    If multiple are found we throw an HTTP 500 internal server error.
    If no result is found return None.

    Args:
        db (Session): a database session that the row will be retrieved from.
        Schema (Base): the SQLAlchemy schema that relates to the table in the database the row will be retrieved from.
        kwargs (optional): additional keyword arguments that will be used as filters in the query.

    Raises:
        HTTP_500_INTERNAL_SERVER_ERROR: this is raised when multiple records are returned
        
    Returns:
        Base: returns a database record.
    """    
    try:
        db_record: Optional[T] = db.query(Schema).filter(*criterion).one()
    except MultipleResultsFound:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Multiple records found",
            )
    except NoResultFound:
        return None
    
    return db_record

def get_records(db: Session, Schema: T, *criterion)-> Optional[List[T]]:
    """Retrieve a list of records from a database.

    Args:
        db (Session): the database session to retrieve the records from.
        Schema (T): the schema type to retrieve.

    Returns:
        Optional[List[T]]: a list of the given schema type records or None if no records were found.
    """
    db_records: List[T] = list(db.query(Schema).filter(*criterion))
    
    
    if(len(db_records) == 0):
        return None
    
    return db_records

def get_record_with_not_found_raise(db: Session, Schema: T, detail: str, *criterion) -> T:
    """Retrieves the a single record from a database that matches a set of filters.

    Args:
        db (Session): a database session that the row will be retrieved from.
        Schema (Base): the SQLAlchemy schema that relates to the table in the database the row will be retrieved from.
        kwargs (optional): additional keyword arguments that will be used as filters in the query.

    Raises: 
        HTTP_404_NOT_FOUND: this is raised when no record is found
        HTTP_500_INTERNAL_SERVER_ERROR: this is raised when multiple records are returned
    
    Returns:
        Base: returns a database record.
    """
    db_record = get_record(db, Schema, *criterion)
    
    if(db_record is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
        
    return db_record