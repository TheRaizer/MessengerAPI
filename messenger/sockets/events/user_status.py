from typing import Any, Dict, List, Tuple
from messenger_schemas.schema import DatabaseSessionContext
from messenger_schemas.schema.user_schema import UserSchema

from messenger.helpers.dependencies.queries.query_friends import (
    query_friends,
)
from messenger.helpers.pubsub.subscriber import Subscriber
from messenger.models.socketio.connection_params import (
    OnConnectionParams,
    OnDisconnectionParams,
)
from messenger.models.socketio.status_change import (
    StatusChangeEventData,
)
from messenger.sockets import (
    sio,
)

from messenger.sockets.events.event_system import (
    socket_event_aggregator,
)


def get_friendlist_ids(
    current_user_id: int,
) -> List[Tuple[int,]]:
    """Retrieves a list of ids of friendships accepted between
        the current user and the friend using a context manager.

    Args:
        current_user_id (int): the id of the current user

    Returns:
        List[Tuple[int,]]: the ids of friendships accepted between
        the current user and the friend.
    """
    with DatabaseSessionContext() as db:
        current_user = UserSchema(user_id=current_user_id)

        friends_table = query_friends(current_user, db)
        friend_ids = db.query(friends_table.user_id).all()

        return friend_ids


async def emit_status_to_friends(_: str, current_user_id: int) -> None:
    """Emits to all active friends that the we are active.

    Args:
        sid (str): socket unique identifier
        current_user_id (int): current user corrosponding to sid
    """
    friend_ids = get_friendlist_ids(current_user_id)

    # notify friends of your status change from offline to some custom status
    for (friend_id,) in friend_ids:
        await sio.emit(
            "ping status change",
            StatusChangeEventData(
                user_id=current_user_id, status="active"
            ).dict(),
            to=friend_id,
        )


async def pong_status_change(_, data: Dict[str, Any]):
    """When a user comes online he emits an event to all friends about their status.
    Each friend upon hearing this new status (through listening to the "status change" event),
    should send back their status through this event.

    data contains your status, id,
    and the user id of the friend to broadcast this info too.
    when we recieve a friend status update we will emit the new update too the client
    """

    await sio.emit(
        "friend status changed",
        StatusChangeEventData(**data).dict(),
        to=data["friend_id"],
    )


sio.on("pong status change", handler=pong_status_change)


async def on_connect_emit_user_status(connection_params: OnConnectionParams):
    await emit_status_to_friends(
        connection_params.sid, connection_params.current_user_id
    )


async def on_disconnect_emit_user_status(
    connection_params: OnDisconnectionParams,
):
    # notify friends of your status change to offline
    session = await sio.get_session(connection_params.sid)
    friend_ids = get_friendlist_ids(session["user_id"])
    for (friend_id,) in friend_ids:
        await sio.emit(
            "ping status change",
            StatusChangeEventData(
                user_id=session["user_id"], status="offline"
            ).dict(),
            to=friend_id,
        )


Subscriber(
    OnConnectionParams, on_connect_emit_user_status, socket_event_aggregator
).subscribe()
Subscriber(
    OnDisconnectionParams,
    on_disconnect_emit_user_status,
    socket_event_aggregator,
).subscribe()
