import logging
import socketio
from messenger.settings import origins


logger = logging.getLogger(__name__)


sio = socketio.AsyncServer(
    cors_allowed_origins=origins,
    async_mode="asgi",
    logger=True,
    engineio_logger=True,
)
sio_app = socketio.ASGIApp(sio)


@sio.event
def connect(sid, _):
    logger.info("Socket connected with sid %s", sid)
