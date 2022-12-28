import socketio
from messenger.settings import origins

sio = socketio.AsyncServer(
    cors_allowed_origins=origins,
    async_mode="asgi",
    logger=True,
    engineio_logger=True,
)
sio_app = socketio.ASGIApp(sio)
