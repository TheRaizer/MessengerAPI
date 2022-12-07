from datetime import (
    datetime,
)
import logging
from operator import (
    attrgetter,
)
from typing import (
    Literal,
    Optional,
)
from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy import (
    and_,
    or_,
)
from sqlalchemy.orm import (
    Session,
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
from messenger.constants.friendship_status_codes import (
    FriendshipStatusCode,
)
from messenger.helpers.db import (
    DatabaseHandler,
)
from messenger.helpers.user_handler import (
    UserHandler,
)


logger = logging.getLogger(__name__)


class FriendshipHandler(DatabaseHandler):
    """Contains basic functionality that is often used to read/write to a friendship record."""

    def __init__(
        self,
        db: Session,
        friendship: Optional[FriendshipSchema] = None,
    ):
        """Initializes an instance of a FriendshipService

        Args:
            db (Session): the database session to use.

            friendship (Optional[FriendshipSchema]): the friendship record
            that will be used during any of the service methods.
        """
        super().__init__(db)
        self.friendship = friendship

    def get_latest_friendship_status(
        self,
    ) -> Optional[FriendshipStatusSchema]:
        """Uses sqlalchemy ORM to query all friendship statuses of self.friendship.
        Returns the last added friendship status.

        Returns:
            Optional[FriendshipStatusSchema]: the last added friendship status
        """
        if self.friendship is None or len(self.friendship.statuses) == 0:
            return None

        return max(
            self.friendship.statuses,
            key=attrgetter("specified_date_time"),
        )

    def raise_if_blocked(
        self,
    ) -> None:
        """Raise 400 http exception if self.friendship is blocked.

        Raises:
            HTTPException: 400 status detailing that the friendship is blocked.
        """

        latest_status = self.get_latest_friendship_status()

        if (
            latest_status is not None
            and latest_status.status_code_id
            == FriendshipStatusCode.BLOCKED.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="friendship is blocked",
            )

    def add_new_status(
        self,
        requester_id: int,
        addressee_id: int,
        specifier_id: int,
        new_status_code_id: FriendshipStatusCode,
    ):
        """Adds a new friendship status to the database.

        Args:
            requester_id (str): the user_id of the friendship requester
            addressee_id (str): the user_id of the friendship addressee
            specifier_id (str): the user_id of the user specifying this new status.
            new_status_code_id (FriendshipStatusCode): the new status code id.

        Returns:
            FriendshipStatusSchema: the new friendship status that was added to the database.
        """
        new_status = FriendshipStatusSchema(
            requester_id=requester_id,
            addressee_id=addressee_id,
            specified_date_time=datetime.now(),
            status_code_id=new_status_code_id.value,
            specifier_id=specifier_id,
        )

        self._db.add(new_status)

        logger.info(
            "(requester_id: %s, addressee_id: %s, status_code_id: %s) add \
            friendship status to session.",
            new_status.requester_id,
            new_status.addressee_id,
            new_status.status_code_id,
        )

        return new_status

    def get_friendship_bidirectional_query(
        self,
        user_id_a: int,
        user_id_b: int,
    ) -> FriendshipSchema:
        """Retrieves a friendship where either user_a is the
        requester and user_b is the addressee or vice-versa. Stores
        the result in self.friendship and returns it. Throws http 404
        exception if no friendship is found.

        Args:
            user_a (int): the id of a user participating in the friendship
            user_b (int): the id of a user participating in the friendship

        Returns:
            Union[Type[FriendshipSchema], None]: the friendship
                record or None if no friendship was found.
        """
        filter_a = and_(
            FriendshipSchema.requester_id == user_id_a,
            FriendshipSchema.addressee_id == user_id_b,
        ).self_group()
        filter_b = and_(
            FriendshipSchema.requester_id == user_id_b,
            FriendshipSchema.addressee_id == user_id_a,
        ).self_group()

        self.friendship = self._get_record_with_not_found_raise(
            FriendshipSchema,
            "friendship was not found",
            or_(
                *[
                    filter_a,
                    filter_b,
                ]
            ),
        )

        return self.friendship


def address_friendship_request(
    friendship_handler: FriendshipHandler,
    new_status_code_id: Literal[
        FriendshipStatusCode.ACCEPTED,
        FriendshipStatusCode.DECLINED,
    ],
) -> FriendshipStatusSchema:
    """Addresses a friendship request by either accepting or declining it.

    Args:
        friendship_service (FriendshipService): the friendship service that will
            be used to add the new status.
        new_status_code_id (Literal[FriendshipStatusCode.ACCEPTED, FriendshipStatusCode.DECLINED]):
            either accept or decline

    Raises:
        HTTPException: If the friendship was already addressed,
            or the friendship is blocked

    Returns:
        FriendshipStatusSchema: the new status that was created.
    """
    friendship_handler.raise_if_blocked()
    latest_status = friendship_handler.get_latest_friendship_status()

    if latest_status is not None and (
        latest_status.status_code_id == FriendshipStatusCode.ACCEPTED.value
        or latest_status.status_code_id == FriendshipStatusCode.DECLINED.value
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="friend request already addressed",
        )

    return friendship_handler.add_new_status(
        friendship_handler.friendship.requester_id,
        friendship_handler.friendship.addressee_id,
        friendship_handler.friendship.addressee_id,
        new_status_code_id,
    )


def address_friendship_request_as_route(
    db: Session,
    current_user_id: int,
    requester_username: str,
    new_status_code_id: Literal[
        FriendshipStatusCode.ACCEPTED,
        FriendshipStatusCode.DECLINED,
    ],
):
    """Addresses a friendship by either accepting or declining it.

    Args:
        db (Session): the database session that will be used to add a new
            friendship status to the DB.
        current_user (UserSchema): the current active user.
        requester_username (str): the username of the user that requested the
            friendship that the current_user will either accept or decline.
        new_status_code_id (Literal[ FriendshipStatusCode.ACCEPTED,
            FriendshipStatusCode.DECLINED, ]): either accept or decline
    """
    addressee_handler = UserHandler(db)
    addressee = addressee_handler.get_user(
        UserSchema.username == requester_username
    )

    friendship_handler = FriendshipHandler(db)

    friendship_handler.get_friendship_bidirectional_query(
        addressee.user_id,
        current_user_id,
    )

    address_friendship_request(
        friendship_handler,
        new_status_code_id,
    )
