from typing import Union
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import Base

def filter_first(db: Session, Schema: Base, **kwargs):
    """Retrieves the first record from a database that matches a set of filters.

    Args:
        db (Session): a database session that the row will be retrieved from.
        Schema (Base): the SQLAlchemy schema that relates to the table in the database the row will be retrieved from.
        kwargs (optional): additional keyword arguments that will be used as filters in the query.

    Returns:
        UserSchema: returns the currently active user.
    """
    db_record: Union[Schema, None] = db.query(Schema).filter_by(**kwargs).first()
    return db_record