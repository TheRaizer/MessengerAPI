from sqlalchemy.orm import sessionmaker, Session
from _submodules.messenger_utils.messenger_schemas.schema import (
    Base,
)
from _submodules.messenger_utils.messenger_schemas.schema import engine


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
