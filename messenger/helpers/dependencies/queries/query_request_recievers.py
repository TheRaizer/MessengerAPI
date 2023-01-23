from fastapi import Depends
from sqlalchemy import func
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


def query_request_recievers(
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Produces a subquery table of all users with whom the current user has sent
    a friendship request too.

    WITH LatestStatus (requester_id, addressee_id, latest_status_code_id) AS (
        SELECT requester_id, addressee_id, status_code_id as latest_status_code_id
        FROM friendship_status
        WHERE friendship_status.specified_date_time IN
        (
                SELECT MAX(specified_date_time) FROM friendship_status
                        WHERE requester_id=18
                        GROUP BY requester_id, addressee_id
        )
    )

    SELECT * FROM LatestStatus
    WHERE latest_status_code_id = "R"

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to query from.
            Defaults to Depends(database_session).
    """

    latest_status_dates = (
        db.query(func.max(FriendshipStatusSchema.specified_date_time))
        .filter(
            FriendshipStatusSchema.requester_id == current_user.user_id,
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

    friend_request_recievers = (
        db.query(UserSchema)
        .select_from(latest_statuses)
        .join(
            UserSchema,
            UserSchema.user_id == latest_statuses.c.addressee_id,
        )
        .filter(
            latest_statuses.c.status_code_id
            == FriendshipStatusCode.REQUESTED.value
        )
        .subquery()
    )

    friend_request_recievers_table_alias = aliased(
        UserSchema, friend_request_recievers
    )

    return friend_request_recievers_table_alias
