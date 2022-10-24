from sqlalchemy import Column, DATETIME, Integer, VARCHAR

from messenger.db.engine import Base

# mimics the user table schema in the actual DB
class User(Base):
    __tablename__ = "user"
    userId = Column(Integer, primary_key=True)
    username = Column(VARCHAR(25))
    firstName = Column(VARCHAR(30))
    lastName = Column(VARCHAR(30))
    birthDate = Column(DATETIME)