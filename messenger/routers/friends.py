from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import FriendshipSchema
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from datetime import datetime
from messenger.helpers.db import filter_first

from messenger.helpers.users import get_current_active_user
from messenger.models.friendship_model import FriendshipModel

router = APIRouter(
    prefix="/friends",
    tags=["friends"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
def get_friendships(current_user: UserSchema = Depends(get_current_active_user)):
    """Retrieves a users friendships, both those requested and those recieved.

    Args:
        current_user (UserSchema, optional): the current signed-in user whose data will be retrieved. Defaults to Depends(get_current_active_user).

    Returns:
        _type_: the friendship requests recieved, and those sent.
    """
    return {"sent": current_user.friend_requests_sent, "recieved": current_user.friend_requests_recieved}

# TODO: create get route to obtain all accepted friendships.

@router.post("/send-request", response_model=FriendshipModel)
def send_friendship_request(username: str, current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(database_session)):
    """Sends a friend request from the current signed-in user to the user with a given username.

    Args:
        username (str): the username of the addressee from the friend request.
        current_user (UserSchema, optional): The current user that will represent the requester of the friend request.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to retrieve the addressee and insert the friendship from/into.
        Defaults to Depends(database_session).

    Returns:
        FriendshipModel: the friendship that was created and inserted into the database.
    """
    addressee = filter_first(db, UserSchema, username=username)
    friendship = FriendshipSchema(requester_id=current_user.user_id, addressee_id=addressee.user_id, created_date_time=datetime.now())
    
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    
    friendship_model = FriendshipModel(**(friendship.__dict__))
    
    return friendship_model