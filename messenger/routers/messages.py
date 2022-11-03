from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_member_schema import GroupChatMemberSchema
from _submodules.messenger_utils.messenger_schemas.schema.message_schema import MessageSchema
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.db import get_record_with_not_found_raise
from messenger.helpers.friends import get_latest_friendship_status, retrieve_friendship_bidirectional_query
from messenger.helpers.users import get_current_active_user
from sqlalchemy.orm import Session
from messenger.models.message_model import CreateMessageModel


router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get('/')
def get_messages():
    return


@router.post("/", status_code=status.HTTP_201_CREATED)
def send_message(addressee_username: str, body: CreateMessageModel, current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(database_session)):
    must_be_their_friend_detail = "you cannot message this person if you are not their friend"
    """Sends a message from the currently signed in user to either another user, or a group chat.
    
    If a group chat id is specified, we will send a message to a group chat, otherwise we will send it to a specified addressee.

    Args:
        addressee_username (str): the username of the user to send a message too.
        current_user (UserSchema, optional): The current user that will represent the sender of the message.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to data from and post data too.
        Defaults to Depends(database_session).

    Returns:
        OKModel: whether the message was successfully sent
    """
    
    if body.group_chat_id:
        # ensure that a db record connecting this user and the group chat exists
        get_record_with_not_found_raise(
                db, 
                GroupChatMemberSchema,
                "not a member of this groupchat", 
                GroupChatMemberSchema.group_chat_id == body.group_chat_id, 
                GroupChatMemberSchema.member_id == current_user.user_id
            )
    else:
        addressee = get_record_with_not_found_raise(db, UserSchema, "addressee with the given username does not exist", UserSchema.username == addressee_username)
        friendship = retrieve_friendship_bidirectional_query(db, current_user, addressee)
        latest_status = get_latest_friendship_status(friendship)

        # friendship must be accepted
        if(not friendship or latest_status.status_code_id != 'A'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=must_be_their_friend_detail,
            )
    
    message = MessageSchema(
            sender_id=current_user.user_id,
            reciever_id=getattr(addressee, 'user_id', None),
            content=body.content,
            created_date_time=datetime.now(),
            group_chat_id=getattr(body, 'group_chat_id', None),
        )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message