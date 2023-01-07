import logging
from typing import Optional
from fastapi import HTTPException
from messenger_schemas.schema import DatabaseSessionContext
from messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.auth.token.auth_tokens import SocketioAccessTokenData
from messenger.helpers.user_handler import UserHandler
from messenger.helpers.auth.token.validate_token import validate_token
from messenger.models.socketio.connection_params import (
    OnConnectionParams,
    OnDisconnectionParams,
)
from messenger.sockets import (
    sio,
)
from messenger.sockets.events.event_system import (
    socket_event_aggregator,
)
from messenger.settings import JWT_SECRET

logger = logging.getLogger(__name__)


@sio.event
async def connect(sid, environ, data):
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

    access_token = ""

    try:
        access_token = data["access_token"]
    except KeyError:
        logger.error(
            "Socket connected with sid %s was unable to send cookie", sid
        )
        await sio.disconnect(sid)
        return

    access_token_data = validate_token(
        access_token, JWT_SECRET, SocketioAccessTokenData
    )

    if access_token_data is None:
        await sio.disconnect(sid)
        return

    current_user: Optional[UserSchema] = None

    with DatabaseSessionContext() as db:
        user_handler = UserHandler(db)

        try:
            current_user = user_handler.get_user(
                UserSchema.user_id == access_token_data.user_id
            )
        except HTTPException:
            logger.info("Invalid credentials for socket with sid %s", sid)
            await sio.disconnect(sid)

    if current_user is None:
        await sio.disconnect(sid)
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
