"""Contains all routes that are friend related."""

from datetime import datetime
import logging
from operator import or_
from typing import List
from bleach import clean
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema import (
    database_session,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import (
    FriendshipSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.helpers.friends import (
    FriendshipHandler,
    address_friendship_request_as_route,
)
from messenger.helpers.users import get_current_active_user
from messenger.helpers.user_handler import UserHandler
from messenger.models.friendship_model import FriendshipModel


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/friends",
    tags=["friends"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get(
    "/requests/recieved",
    status_code=status.HTTP_200_OK,
    response_model=List[FriendshipModel],
)
def get_friendship_requests_recieved(
    current_user: UserSchema = Depends(get_current_active_user),
):
    """Retrieves a users friendship requests recieved

    Args:
        current_user (UserSchema, optional): the current signed-in user
            whose data will be retrieved. Defaults to Depends(get_current_active_user).

    Returns:
        _type_: the friendship requests recieved, and those sent.
    """
    friendship_requests_recieved_models = list(
        map(
            lambda friendship_schema: FriendshipModel(
                requester_id=friendship_schema.requester_id,
                addressee_id=friendship_schema.addressee_id,
                created_date_time=friendship_schema.created_date_time,
            ),
            current_user.friend_requests_recieved,
        )
    )

    return friendship_requests_recieved_models


@router.get(
    "/requests/sent",
    status_code=status.HTTP_200_OK,
    response_model=List[FriendshipModel],
)
def get_friendship_requests_sent(
    current_user: UserSchema = Depends(get_current_active_user),
):
    """Retrieves a users friendship requests sent

    Args:
        current_user (UserSchema, optional): the current signed-in user
            whose data will be retrieved. Defaults to Depends(get_current_active_user).

    Returns:
        _type_: the friendship requests recieved, and those sent.
    """
    friendship_requests_sent_models = list(
        map(
            lambda friendship_schema: FriendshipModel(
                requester_id=friendship_schema.requester_id,
                addressee_id=friendship_schema.addressee_id,
                created_date_time=friendship_schema.created_date_time,
            ),
            current_user.friend_requests_sent,
        )
    )

    return friendship_requests_sent_models


@router.get("/requests/accepted", status_code=status.HTTP_200_OK)
def get_accepted_friendships(
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Produces a list of all friendships that are accepted between
    the current_user and other users. This gives you the standard
    "friends list" of the current user.

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to query from.
            Defaults to Depends(database_session).
    """
    # TODO: get all users from friendships where the addressee or requester
    # is the current user and whose latest friendship status is accepted
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
        current_user (UserSchema, optional): The current user that
            will represent the requester of the friend request.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to retrieve the addressee
            and insert the friendship from/into.
            Defaults to Depends(database_session).

    Returns:
        FriendshipModel: the friendship that was created and inserted into the database.
    """
    addressee_handler = UserHandler(db)
    addressee = addressee_handler.get_user(
        UserSchema.username == clean(username),
    )

    friendship_handler = FriendshipHandler(db)

    friendship = friendship_handler.get_friendship_bidirectional_query(
        current_user, addressee
    )

    if friendship is not None:
        latest_status = friendship_handler.get_latest_friendship_status()

        already_requested_friendship = (
            latest_status is not None
            and friendship.requester_id == current_user.user_id
            and latest_status.status_code_id
            == FriendshipStatusCode.REQUESTED.value
        )

        if already_requested_friendship:
            # you cannot resend a friend request
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you cannot send another friendship request",
            )
        if (
            latest_status is not None
            and latest_status.status_code_id
            != FriendshipStatusCode.REQUESTED.value
        ):
            # you cannot send a friend request if the friendship is blocked,
            # declined, or are already this persons friend
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you cannot send a friendship request",
            )

    new_friendship = FriendshipSchema(
        requester_id=current_user.user_id,
        addressee_id=addressee.user_id,
        created_date_time=datetime.now(),
    )

    new_status = FriendshipStatusSchema(
        requester_id=current_user.user_id,
        addressee_id=addressee.user_id,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=current_user.user_id,
    )

    try:
        db.add(new_friendship)
        logger.info(
            "(requester: %s, addressee: %s) friendship has been\
                successfully inserted into the friendship table",
            new_friendship.requester_id,
            new_friendship.addressee_id,
        )

        db.add(new_status)
        logger.info(
            "(requester: %s, addressee: %s, specified_date_time: %s, status_code_id: %s)\
            friendship status has been successfully inserted into the friendship_status table",
            new_friendship.requester_id,
            new_friendship.addressee_id,
            new_status.specified_date_time,
            new_status.status_code_id,
        )
        db.commit()
        db.refresh(new_friendship)

    except Exception as exc:
        logger.error(
            "failed to insert friendship status or friendship into database due to %s",
            exc,
            exc_info=True,
        )

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
        current_user (UserSchema, optional): The currently signed in user that will be declining
            the friendship
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    address_friendship_request_as_route(
        db, current_user, requester_username, FriendshipStatusCode.ACCEPTED
    )
    db.commit()


@router.post("/requests/decline", status_code=status.HTTP_201_CREATED)
def decline_friendship_request(
    requester_username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Declines a friend request from a given username.

    Args:
        requester_username (str): the username of the user whose friend request you want to decline.
        current_user (UserSchema, optional): The currently signed in user that will be declining
            the friendship.
        Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
        Defaults to Depends(database_session).
    """
    address_friendship_request_as_route(
        db, current_user, requester_username, FriendshipStatusCode.DECLINED
    )
    db.commit()


@router.post("/requests/block", status_code=status.HTTP_201_CREATED)
def block_friendship_request(
    user_to_block_username: str,
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Blocks a user. This command can come from either the requester, or addressee
    of a friendship. Additionally it can be called even when a friendship between
    the two users does not initially exist.

    Args:
        user_to_block_username (str): the username of the user who will be blocked.
        current_user (UserSchema, optional): The currently signed in user that
            will be executing the blocking action. Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to use for database reads/writes.
            Defaults to Depends(database_session).
    """

    friendship_handler = FriendshipHandler(db)
    user_to_block_handler = UserHandler(db)

    user_to_block = user_to_block_handler.get_user(
        UserSchema.username == clean(user_to_block_username)
    )

    # attempt to fetch a friendship record with the current user as either the
    # requester or addressee
    friendship = friendship_handler.get_friendship_bidirectional_query(
        user_to_block, current_user
    )

    # if no friendship record appears, create a new one
    if friendship is None:
        friendship = FriendshipSchema(
            requester_id=current_user.user_id,
            addressee_id=user_to_block.user_id,
            created_date_time=datetime.now(),
        )
        db.add(friendship)
        logger.info(
            "(requester_id: %s, addressee_id: %s) add friendship to session.",
            friendship.requester_id,
            friendship.addressee_id,
        )

        friendship_handler.friendship = friendship
    else:
        friendship_handler.raise_if_blocked()

    # create a new friendship status based on a friendship record with
    # a status code of 'B' == 'Blocked'
    friendship_handler.add_new_status(
        friendship_handler.friendship.requester_id,
        friendship_handler.friendship.addressee_id,
        current_user.user_id,
        FriendshipStatusCode.BLOCKED,
    )

    db.commit()

    logger.info(
        "(requester_id: %s, addressee_id: %s, friendship_status_code_id: %s) add friendship and friendship status to respective tables.",
        friendship.requester_id,
        friendship.addressee_id,
        FriendshipStatusCode.BLOCKED,
    )
