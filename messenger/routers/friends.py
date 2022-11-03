from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import FriendshipSchema
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import FriendshipStatusSchema
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from datetime import datetime
from messenger.helpers.db import get_record_with_not_found_raise
from messenger.helpers.friends import add_new_friendship_status_as_addressee, block_user

from messenger.helpers.users import get_current_active_user
from messenger.models.friendship_model import FriendshipModel

router = APIRouter(
    prefix="/friends",
    tags=["friends"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("/", status_code=status.HTTP_200_OK)
def get_friendships(current_user: UserSchema = Depends(get_current_active_user)):
    """Retrieves a users friendships, both those requested and those recieved.

    Args:
        current_user (UserSchema, optional): the current signed-in user whose data will be retrieved. Defaults to Depends(get_current_active_user).

    Returns:
        _type_: the friendship requests recieved, and those sent.
    """
    return {"sent": current_user.friend_requests_sent, "recieved": current_user.friend_requests_recieved}


@router.post("/requests/send-request", response_model=FriendshipModel, status_code=status.HTTP_201_CREATED)
def send_friendship_request(username: str, current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(database_session)):
    """Sends a friend request from the current signed-in user to the user with a given username.

    Args:
        username (str): the username of the user to send the friend request too.
        current_user (UserSchema, optional): The current user that will represent the requester of the friend request.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to retrieve the addressee and insert the friendship from/into.
        Defaults to Depends(database_session).

    Returns:
        FriendshipModel: the friendship that was created and inserted into the database.
    """
    # TODO: shouldnt be able to send a friendship request to a user that has already sent one to you.
    
    addressee = get_record_with_not_found_raise(db, UserSchema, "no such addressee exists", UserSchema.username == username)
    friendship = FriendshipSchema(requester_id=current_user.user_id, addressee_id=addressee.user_id, created_date_time=datetime.now())
    
    new_status = FriendshipStatusSchema(
        requester_id=current_user.user_id,
        addressee_id=addressee.user_id,
        specified_date_time=datetime.now(),
        status_code_id="R",
        specifier_id=current_user.user_id)
    
    db.add(new_status)
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    
    friendship_model = FriendshipModel(**(friendship.__dict__))
    
    return friendship_model


@router.post("/requests/accept", status_code=status.HTTP_201_CREATED)
def accept_friendship_request(requester_username: str, current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(database_session)):
    """Accepts a friend request from a given username.

    Args:
        requester_username (str): the username of the user whose friend request you want to accept.
        current_user (UserSchema, optional): The currently signed in user that will be declining the friendship
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    add_new_friendship_status_as_addressee(db, requester_username, current_user, "A")


@router.post("/requests/decline", status_code=status.HTTP_201_CREATED)
def accept_friendship_request(requester_username: str, current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(database_session)):
    """Declines a friend request from a given username.

    Args:
        requester_username (str): the username of the user whose friend request you want to decline.
        current_user (UserSchema, optional): The currently signed in user that will be declining the friendship.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    add_new_friendship_status_as_addressee(db, requester_username, current_user, "D")


@router.post("/requests/block", status_code=status.HTTP_201_CREATED)
def accept_friendship_request(user_to_block_username: str, current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(database_session)):
    """Accepts a friend request from a given username.

    Args:
        user_to_block_username (str): the username of the user who will be blocked.
        current_user (UserSchema, optional): The currently signed in user that will be executing the blocking action.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    block_user(db, user_to_block_username, current_user)