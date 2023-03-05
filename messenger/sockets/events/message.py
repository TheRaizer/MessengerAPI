import logging
from typing import Any, Dict
from fastapi import HTTPException
from messenger_schemas.schema import DatabaseSessionContext
from messenger.helpers.send_message import send_message
from messenger.sockets import (
    sio,
)

logger = logging.getLogger(__name__)


async def emit_message(sid, data: Dict[str, Any]):
    """Sends a message to a specific friend.

    This event emits back to the clients whether the message was successful or not.
    In the case it is successful it will emit an event to both the sender and reciever
    of its success. Otherwise it will emit to only the sending client that the
    message failed.

    The response's include a message_tracker_id which is provided by the client.
    This is used to allow the client to identify the message when events are emitted
    back to them.

    The sender is identified using their socketio access token.

    Args:
        sid (str): the identifier for the sending clients socket
        data (Dict[str, Any]): a dictionary containing "content" of the message,
        "group_chat_id", "addressee_username", and "message_tracker_id".
    """
    session = await sio.get_session(sid)
    with DatabaseSessionContext() as db:
        try:
            message_model = send_message(
                db,
                session["user_id"],
                data["content"],
                data["group_chat_id"],
                data["addressee_username"],
            )
        except HTTPException as exc:
            await sio.emit(
                "message response",
                {
                    "detail": exc.detail,
                    "status_code": exc.status_code,
                    "message_tracking_id": data["message_tracking_id"],
                },
                to=sid,
            )
            return

    success_data = (
        {
            "message": message_model.json(),
            "message_tracking_id": data["message_tracking_id"],
        },
    )

    await sio.emit(
        "message response",
        success_data,
        to=message_model.reciever_id,
    )
    await sio.emit(
        "message response",
        success_data,
        to=message_model.sender_id,
    )


sio.on("message", handler=emit_message)
