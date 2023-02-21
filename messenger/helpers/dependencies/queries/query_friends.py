from fastapi import Depends
from sqlalchemy import and_, case, func, or_
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


def query_friends(
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(database_session),
):
    """Produces a subquery table of all users with whom the current user has an
    accepted friendship with. This gives you the standard "friends list"
    of the current user.

    The ORM queries are based off the following SQL which will get all the usernames
    of the users that have accepted friendship requests with the current user or have had
    their friendship request accepted by the current user.

    SELECT username
    FROM friendship_status fs
    INNER JOIN (
        SELECT requester_id, addressee_id, MAX(specified_date_time) as max_date_time
        FROM friendship_status
        WHERE addressee_id=:current_user_id OR requester_id=:current_user_id
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
    WHERE fs.status_code_id = "A"

    Args:
        current_user (UserSchema, optional): the currently signed in user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): the database session to query from.
            Defaults to Depends(database_session).
    """

    # Get all the requester and addressee id's from friendships where the addressee or requester
    # is the current user and whose latest friendship status code is accepted
    latest_status_dates = (
        db.query(
            FriendshipStatusSchema.requester_id,
            FriendshipStatusSchema.addressee_id,
            func.max(FriendshipStatusSchema.specified_date_time).label(
                "max_date_time"
            ),
        )
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
        .subquery()
    )

    accepted_friends_table = (
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
            == FriendshipStatusCode.ACCEPTED.value
        )
        .subquery()
    )

    # alias the accepted friends table so its queried results are mapped to UserSchema
    # this essentially casts the generic subquery table to a UserSchema table
    accepted_friends_table_alias = aliased(UserSchema, accepted_friends_table)

    return accepted_friends_table_alias
