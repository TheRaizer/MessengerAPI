from operator import or_
from bleach import clean
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import database_session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from datetime import datetime
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.helpers.friends import (
    FriendshipHandler,
    address_friendship_request_as_route,
)
from messenger.helpers.users import get_current_active_user
from messenger.helpers.user_handler import UserHandler
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
    return {
        "sent": current_user.friend_requests_sent,
        "recieved": current_user.friend_requests_recieved,
    }


@router.get("/requests/accepted", status_code=status.HTTP_200_OK)
def get_accepted_friendships(
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    # TODO: get all users from friendships where the addressee or requester is the current user and whose latest friendship status is accepted
    db.query(FriendshipSchema).select_from(FriendshipSchema).where(
        or_(
            FriendshipSchema.addressee_id == current_user.user_id,
            FriendshipSchema.requester_id == current_user.user_id,
        )
    )


@router.post(
    "/requests/send-request",
    response_model=FriendshipModel,
    status_code=status.HTTP_201_CREATED,
)
def send_friendship_request(
    username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
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
    addressee_handler = UserHandler(db)
    addressee_handler.get_user(
        UserSchema.username == clean(username),
    )

    friendship_handler = FriendshipHandler(db)

    friendship = friendship_handler.get_friendship_bidirectional_query(
        current_user, addressee_handler.user
    )

    if friendship is not None:
        latest_status = friendship_handler.get_latest_friendship_status()

        already_requested_friendship = (
            friendship.requester_id == current_user.user_id
            and latest_status.status_code_id == FriendshipStatusCode.REQUESTED.value
        )

        if already_requested_friendship:
            # you cannot resend a friend request
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you cannot send another friendship request",
            )
        elif latest_status.status_code_id != FriendshipStatusCode.REQUESTED.value:
            # you cannot send a friend request if the friendship is blocked, declined, or are already this persons friend
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you cannot send a friendship request",
            )

    new_friendship = FriendshipSchema(
        requester_id=current_user.user_id,
        addressee_id=addressee_handler.user.user_id,
        created_date_time=datetime.now(),
    )

    new_status = FriendshipStatusSchema(
        requester_id=current_user.user_id,
        addressee_id=addressee_handler.user.user_id,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=current_user.user_id,
    )

    db.add(new_friendship)
    db.add(new_status)
    db.commit()
    db.refresh(new_friendship)

    friendship_model = FriendshipModel(
        requester_id=new_friendship.requester_id,
        addressee_id=new_friendship.addressee_id,
        created_date_time=new_friendship.created_date_time,
    )

    return friendship_model


@router.post("/requests/accept", status_code=status.HTTP_201_CREATED)
def accept_friendship_request(
    requester_username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Accepts a friend request from a given username.

    Args:
        requester_username (str): the username of the user whose friend request you want to accept.
        current_user (UserSchema, optional): The currently signed in user that will be declining the friendship
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    address_friendship_request_as_route(
        db, current_user, requester_username, FriendshipStatusCode.ACCEPTED
    )


@router.post("/requests/decline", status_code=status.HTTP_201_CREATED)
def decline_friendship_request(
    requester_username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Declines a friend request from a given username.

    Args:
        requester_username (str): the username of the user whose friend request you want to decline.
        current_user (UserSchema, optional): The currently signed in user that will be declining the friendship.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    address_friendship_request_as_route(
        db, current_user, requester_username, FriendshipStatusCode.DECLINED
    )


@router.post("/requests/block", status_code=status.HTTP_201_CREATED)
def block_friendship_request(
    user_to_block_username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Blocks a user. This command can come from either the requester, or addressee of a friendship. Additionally it can be
    called even when a friendship between the two users does not initially exist.

    Args:
        user_to_block_username (str): the username of the user who will be blocked.
        current_user (UserSchema, optional): The currently signed in user that will be executing the blocking action.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """

    friendship_handler = FriendshipHandler(db)
    user_to_block_handler = UserHandler(db)

    user_to_block_handler.get_user(UserSchema.username == clean(user_to_block_username))

    # attempt to fetch a friendship record with the current user as either the requester or addressee
    friendship = friendship_handler.get_friendship_bidirectional_query(
        user_to_block_handler.user, current_user
    )

    # if no friendship record appears, create a new one
    if friendship is None:
        friendship = FriendshipSchema(
            requester_id=current_user.user_id,
            addressee_id=user_to_block_handler.user.user_id,
            created_date_time=datetime.now(),
        )
        db.add(friendship)

        friendship_handler.friendship = friendship
    else:
        friendship_handler.raise_if_blocked()

    # create a new friendship status based on a friendship record with a status code of 'B' == 'Blocked'
    friendship_handler.add_new_status(
        friendship_handler.friendship.requester_id,
        friendship_handler.friendship.addressee_id,
        current_user.user_id,
        FriendshipStatusCode.BLOCKED,
    )

    db.commit()
