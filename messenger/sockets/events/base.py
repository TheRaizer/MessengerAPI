import logging
from typing import Optional
import urllib.parse
from fastapi import HTTPException
from messenger_schemas.schema import DatabaseSessionContext
from messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.users import get_current_user
from messenger.sockets import (
    sio,
)
from messenger.sockets.events.event_system import (
    OnConnectionParams,
    OnDisconnectionParams,
    socket_event_aggregator,
)

logger = logging.getLogger(__name__)


@sio.event
async def connect(sid, environ):
    """During connection we must verify that the user has authentication.
    If they are not we disconnect the socket.

    Otherwise We will also create a room with their user_id and publish
    any subscribers to the on connection params.

    We then add a disconnect event which will publish any subscribers to
    the disconnection params.

    Args:
        sid (_type_): the sockets unique identified
        environ (_type_): the environment of the socket
    """

    query_params = urllib.parse.parse_qs(environ["QUERY_STRING"])
    access_token = query_params["access_token"][0]

    current_user: Optional[UserSchema] = None

    with DatabaseSessionContext() as db:
        try:
            current_user = get_current_user(db, access_token)
        except HTTPException:
            logger.info("Invalid credentials for socket with sid %s", sid)
            await sio.disconnect(sid)

    if current_user is None:
        return

    logger.info("Socket connected with sid %s", sid)

    await sio.save_session(sid, {"user_id": current_user.user_id})
    sio.enter_room(sid, current_user.user_id)

    await socket_event_aggregator.publish(
        OnConnectionParams(sid=sid, current_user_id=current_user.user_id)
    )

    @sio.event
    async def disconnect(sid):
        await socket_event_aggregator.publish(OnDisconnectionParams(sid=sid))
