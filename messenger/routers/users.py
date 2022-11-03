from fastapi import APIRouter, Depends, status
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema

from messenger.models.user_model import UserModel
from messenger.helpers.users import get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/", response_model=UserModel, status_code=status.HTTP_200_OK)
def get_current_user(current_user: UserSchema = Depends(get_current_active_user)):
    """Retrieves the current user from the database, if none is found an unauthorized error is thrown.

    Args:
        current_user (UserSchema, optional): the currently signed in user.
        Defaults to Depends(get_current_active_user).

    Returns:
        OKModel[UserModel]: standard ok data and the users data excluding any sensitive data.
    """
    user: UserModel = UserModel(**(current_user.__dict__))
    return user