from sqlalchemy.orm import sessionmaker
from messenger_schemas.schema import (
    Base,
)

# import all the schemas as to load the Base with all the schema metadata
import messenger_schemas.schema.schemas
from messenger_schemas.schema import engine

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
