from sqlalchemy.orm import sessionmaker
from _submodules.messenger_utils.messenger_schemas.schema import (
    Base,
)

# import all the schemas as to load the Base with all the schema metadata
import _submodules.messenger_utils.messenger_schemas.schema.schemas
from _submodules.messenger_utils.messenger_schemas.schema import engine

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
