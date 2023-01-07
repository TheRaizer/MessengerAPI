from fastapi import Depends
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, aliased
from messenger_schemas.schema import (
    database_session,
)
from messenger_schemas.schema.friendship_status_schema import (
    FriendshipStatusSchema,
)
from messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.constants.friendship_status_codes import FriendshipStatusCode
from messenger.helpers.dependencies.user import get_current_active_user


def query_accepted_friendships(
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Produces a subquery table of all users with whom the current user has an
    accepted friendship with. This gives you the standard "friends list"
    of the current user.

    The ORM queries are based off the following SQL which will get all the usernames
    of the users that have accepted friendship requests with the current user or have had
    their friendship request accepted by the current user.

    WITH LatestStatus (requester_id, addressee_id, latest_status_code_id) AS (
        SELECT requester_id, addressee_id, status_code_id as latest_status_code_id
        FROM friendship_status
        WHERE friendship_status.specified_date_time IN
        (
                SELECT MAX(specified_date_time) FROM friendship_status
                        WHERE (addressee_id=18 OR requester_id=18)
                        GROUP BY requester_id, addressee_id
        )
    )

    SELECT username FROM LatestStatus
    INNER JOIN user ON
        (
            LatestStatus.addressee_id=user.user_id
            AND
            LatestStatus.addressee_id != :current_user_id
        )
        OR
        (
            LatestStatus.requester_id=user.user_id
            AND
            LatestStatus.requester_id != :current_user_id)
    WHERE LatestStatus.latest_status_code_id = "A";

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to query from.
            Defaults to Depends(database_session).
    """

    # Get all the requester and addressee id's from friendships where the addressee or requester
    # is the current user and whose latest friendship status code is accepted
    latest_status_dates = (
        db.query(func.max(FriendshipStatusSchema.specified_date_time))
        .filter(
            or_(
                FriendshipStatusSchema.addressee_id == current_user.user_id,
                FriendshipStatusSchema.requester_id == current_user.user_id,
            ),
        )
        .group_by(
            FriendshipStatusSchema.addressee_id,
            FriendshipStatusSchema.requester_id,
        )
    )

    latest_statuses = (
        db.query(FriendshipStatusSchema)
        .with_entities(
            FriendshipStatusSchema.requester_id,
            FriendshipStatusSchema.addressee_id,
            FriendshipStatusSchema.status_code_id,
        )
        .filter(
            FriendshipStatusSchema.specified_date_time.in_(latest_status_dates)
        )
        .subquery()
    )

    accepted_friends_table = (
        db.query(UserSchema)
        .select_from(latest_statuses)
        .join(
            UserSchema,
            or_(
                and_(
                    UserSchema.user_id == latest_statuses.c.requester_id,
                    latest_statuses.c.requester_id != current_user.user_id,
                ),
                and_(
                    UserSchema.user_id == latest_statuses.c.addressee_id,
                    latest_statuses.c.addressee_id != current_user.user_id,
                ),
            ),
        )
        .filter(
            latest_statuses.c.status_code_id
            == FriendshipStatusCode.ACCEPTED.value
        )
        .subquery()
    )

    # alias the accepted friends table so its queried results are mapped to UserSchema
    # this essentially casts the generic subquery table to a UserSchema table
    accepted_friends_table_alias = aliased(UserSchema, accepted_friends_table)

    return accepted_friends_table_alias
