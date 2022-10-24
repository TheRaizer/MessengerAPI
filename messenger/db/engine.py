from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy import create_engine
from messenger.environmentVariables import RDS_ENDPOINT, USER, PASSWORD, PORT, NAME
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

# there is no readonly replica of DB because aws is being a pain in the ass.
Base: DeclarativeMeta = declarative_base()

engine = create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{RDS_ENDPOINT}:{PORT}/{NAME}"
)

# make this function a context manager that has specific functionality built in which closes the session after each use.
# will be referenced with the 'with' keyword
@contextmanager
def database_session():
    session: Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    
    try:
        yield session
        if session.dirty:
            session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
    