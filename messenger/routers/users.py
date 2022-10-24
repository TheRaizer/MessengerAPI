from fastapi import APIRouter

from messenger.db.engine import database_session
from messenger.db.schema.tables.User import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{user_id}")
def get_user(user_id: int):
    with database_session() as session:
        user = session.query(User).get({"userId": user_id})
        return user