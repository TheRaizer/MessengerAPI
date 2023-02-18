import logging
from typing import Any, Dict
from messenger_schemas.schema import DatabaseSessionContext
from messenger.helpers.send_message import send_message
from messenger.sockets import (
    sio,
)
from messenger.sockets.helpers.validate_access_token import (
    validate_access_token,
)

logger = logging.getLogger(__name__)


async def emit_message(sid, _, data: Dict[str, Any]):
    access_token_data = await validate_access_token(sid, data)

    if access_token_data is None or access_token_data.user_id is None:
        return

    with DatabaseSessionContext() as db:
        message_model = send_message(
            db,
            access_token_data.user_id,
            data["content"],
            data["group_chat_id"],
            data["addressee_username"],
        )

    await sio.emit(
        "message response", message_model, to=message_model.reciever_id
    )


sio.on("send message", handler=emit_message)
