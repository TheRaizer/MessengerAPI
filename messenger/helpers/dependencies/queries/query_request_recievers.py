from fastapi import Depends
from sqlalchemy import and_, case, func
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

    SELECT username
    FROM friendship_status fs
    INNER JOIN (
        SELECT requester_id, addressee_id, MAX(specified_date_time) as max_date_time
        FROM friendship_status
        WHERE requester_id=:current_user_id
        GROUP BY requester_id, addressee_id
    ) latest_status
    ON fs.requester_id = latest_status.requester_id
    AND fs.addressee_id = latest_status.addressee_id
    AND fs.specified_date_time = latest_status.max_date_time
    INNER JOIN user
    ON user.user_id = CASE
        WHEN fs.addressee_id = :current_user_id THEN fs.requester_id
        ELSE fs.addressee_id
    END
    WHERE fs.status_code_id = "R"

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to query from.
            Defaults to Depends(database_session).
    """

    latest_status_dates = (
        db.query(
            FriendshipStatusSchema.requester_id,
            FriendshipStatusSchema.addressee_id,
            func.max(FriendshipStatusSchema.specified_date_time).label(
                "max_date_time"
            ),
        )
        .filter(
            FriendshipStatusSchema.requester_id == current_user.user_id,
        )
        .group_by(
            FriendshipStatusSchema.addressee_id,
            FriendshipStatusSchema.requester_id,
        )
        .subquery()
    )

    friend_request_recievers = (
        db.query(UserSchema)
        .select_from(FriendshipStatusSchema)
        .join(
            latest_status_dates,
            and_(
                FriendshipStatusSchema.requester_id
                == latest_status_dates.c.requester_id,
                FriendshipStatusSchema.addressee_id
                == latest_status_dates.c.addressee_id,
                FriendshipStatusSchema.specified_date_time
                == latest_status_dates.c.max_date_time,
            ),
        )
        .join(
            UserSchema,
            UserSchema.user_id
            == case(
                (
                    FriendshipStatusSchema.addressee_id == current_user.user_id,
                    FriendshipStatusSchema.requester_id,
                ),
                else_=FriendshipStatusSchema.addressee_id,
            ),
        )
        .filter(
            FriendshipStatusSchema.status_code_id
            == FriendshipStatusCode.REQUESTED.value
        )
        .subquery()
    )

    friend_request_recievers_table_alias = aliased(
        UserSchema, friend_request_recievers
    )

    return friend_request_recievers_table_alias
