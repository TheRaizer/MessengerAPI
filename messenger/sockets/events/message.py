import logging
from typing import Any, Dict
from fastapi import HTTPException
from messenger_schemas.schema import DatabaseSessionContext
from messenger.helpers.send_message import send_message
from messenger.sockets import (
    sio,
)
from messenger.sockets.helpers.validate_access_token import (
    validate_access_token,
)

logger = logging.getLogger(__name__)


async def emit_message(sid, data: Dict[str, Any]):
    access_token_data = await validate_access_token(sid, data)

    if access_token_data is None or access_token_data.user_id is None:
        return

    with DatabaseSessionContext() as db:
        try:
            message_model = send_message(
                db,
                access_token_data.user_id,
                data["content"],
                data["group_chat_id"],
                data["addressee_username"],
            )
        except HTTPException as exc:
            await sio.emit(
                "message response",
                {"detail": exc.detail, "status_code": exc.status_code},
                to=sid,
            )
            return

    await sio.emit(
        "message response", message_model.json(), to=message_model.reciever_id
    )


sio.on("message", handler=emit_message)
