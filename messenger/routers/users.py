from fastapi import APIRouter, Depends
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema

from messenger.models.user_model import UserModel
from messenger.helpers.users import get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me", response_model=UserModel)
def get_current_user(current_user: UserSchema = Depends(get_current_active_user)):
    user: UserModel = UserModel(**(current_user.__dict__))
    return user