from datetime import datetime
from operator import attrgetter
from typing import Literal, Type, Union
from fastapi import HTTPException, status

from sqlalchemy import and_, or_
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import FriendshipSchema
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import FriendshipStatusSchema
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.db import get_record, get_record_with_not_found_raise
from sqlalchemy.orm import Session

def raise_if_blocked(friendship: FriendshipSchema) -> None:
    latest_status = get_latest_friendship_status(friendship)
    
    if(latest_status.status_code_id == "B"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="friendship is blocked",
        )

def retrieve_friendship_bidirectional_query(db: Session, user_a: UserSchema, user_b: UserSchema) -> Union[Type[FriendshipSchema], None]:
    """Retrieves a friendship where either user_a is the requester and user_b is the addressee or vice-versa.

    Args:
        db (Session): the database session to retreive the friendship from
        user_a (UserSchema): a user participating in the friendship
        user_b (UserSchema): a user participating in the friendship

    Returns:
        Union[Type[FriendshipSchema], None]: the friendship record or None if no friendship was found.
    """
    a = and_(FriendshipSchema.requester_id == user_a.user_id, FriendshipSchema.addressee_id == user_b.user_id).self_group()
    b = and_(FriendshipSchema.requester_id == user_b.user_id, FriendshipSchema.addressee_id == user_a.user_id).self_group()
    
    friendship = get_record(
                db,
                FriendshipSchema,
                or_(*[a, b]),
            )
    return friendship


def get_latest_friendship_status(friendship: FriendshipSchema) -> FriendshipStatusSchema:
    return max(friendship.statuses, key=attrgetter('specified_date_time'))


def add_new_friendship_status_as_addressee(db: Session, requester_username: str, current_user: UserSchema, new_status_code_id: Literal["A", "D"]) -> None:
    """Allows the current signed in user to either accept or decline a friendship request.

    Args:
        db (Session): the database session that the new status will be added too.
        requester_username (str): the username of the friendship requester
        current_user (UserSchema): the currently signed in user
        new_status_code_id (Literal["A", "D"]): the new status code id either "A" == "Accepted" or "D" == "Declined"
    """
    requester = get_record_with_not_found_raise(db, UserSchema, "no such friend requester exists", UserSchema.username == requester_username)
    
    # a friendship must exist
    friendship = get_record_with_not_found_raise(
        db,
        FriendshipSchema,
        "no such friend request exists",
        and_(FriendshipSchema.requester_id == requester.user_id, FriendshipSchema.addressee_id == current_user.user_id))
    
    raise_if_blocked(friendship)
    
    latest_status = get_latest_friendship_status(friendship)
    
    if(latest_status.status_code_id == "A"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="friend request already accepted",
        )
    
    new_status = FriendshipStatusSchema(
        requester_id=requester.user_id,
        addressee_id=current_user.user_id,
        specified_date_time=datetime.now(),
        status_code_id=new_status_code_id,
        specifier_id=current_user.user_id)
    
    db.add(new_status)
    db.commit()
    
def block_user(db: Session, user_to_block_username: str, current_user: UserSchema) -> None:
    """Blocks a user. This command can come from either the requester, or addressee of a friendship. Additionally it can be
    called even when a friendship between the two users does not exist.

    Args:
        db (Session): the db session where a new friendship might be created, and a new status with the blocked status code will be created.
        user_to_block_username (str): the username of the user to block.
        current_user (UserSchema): the current signed in user who will be blocking someone.
    """
    user_to_block = get_record_with_not_found_raise(db, UserSchema, "no such user to block exists", UserSchema.username == user_to_block_username)
    
    # attempt to fetch a friendship record with the current user as either the requester or addressee
    friendship = retrieve_friendship_bidirectional_query(db, user_to_block, current_user)
    
    raise_if_blocked(friendship)
    
    # if no friendship record appears, create a new one
    if(friendship is None):
        friendship = FriendshipSchema(requester_id=current_user.user_id, addressee_id=user_to_block.user_id, created_date_time=datetime.now())
        db.add(friendship)
    
    # create a new friendship status based on a friendship record with a status code of 'B' == 'Blocked'
    new_status = FriendshipStatusSchema(
        requester_id=friendship.requester_id,
        addressee_id=friendship.addressee_id,
        specified_date_time=datetime.now(),
        status_code_id="B",
        specifier_id=current_user.user_id)
    
    db.add(new_status)
    db.commit()
    
#TODO: unblocking. Which can only occur if the current signed in user who wishes to unblock, is the specifier of the blocking status.
