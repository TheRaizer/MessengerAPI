import logging
from typing import Any, Optional
from messenger.helpers.tokens.validate_token import validate_token
from messenger.models.fastapi.socketio_access_token_data import (
    SocketioAccessTokenData,
)
from messenger.settings import JWT_SECRET
from messenger.sockets import (
    sio,
)

logger = logging.getLogger(__name__)


async def validate_access_token(
    sid: str, data: Any
) -> Optional[SocketioAccessTokenData]:
    access_token = ""

    try:
        access_token = data["access_token"]
    except KeyError:
        logger.error(
            "Socket connected with sid %s was unable to send cookie", sid
        )
        await sio.disconnect(sid)
        return None

    access_token_data = validate_token(
        access_token, JWT_SECRET, SocketioAccessTokenData
    )

    if access_token_data is None:
        await sio.disconnect(sid)
        return None

    return access_token_data
