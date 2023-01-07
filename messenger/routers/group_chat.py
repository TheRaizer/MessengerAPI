"""Contains routes for group chats."""

from fastapi import APIRouter, Depends, status
from messenger_schemas.schema.group_chat_schema import (
    GroupChatSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)

from messenger.helpers.dependencies.user import get_current_active_user
from messenger.models.fastapi.group_chat_model import CreateGroupChatModel

router = APIRouter(
    prefix="/group_chats",
    tags=["group_chats"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.post("/", status_code=status.HTTP_200_OK)
def create_group_chat(
    body: CreateGroupChatModel,
    current_user: UserSchema = Depends(get_current_active_user),
):
    group_chat = GroupChatSchema(name=body.group_chat_name)
    pass
