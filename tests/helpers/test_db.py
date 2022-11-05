from sqlalchemy.orm import Session

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.db import get_record

def test_get_record(session: Session):
    user = UserSchema(username="some-user", password_hash="some-hash", email="some-email")
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    retrieved_user = get_record(session, UserSchema, UserSchema.username=="some-user")
    
    assert user.user_id == retrieved_user.user_id
        