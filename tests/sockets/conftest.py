from typing import List, Optional

import asyncio

import pytest
import uvicorn

from fastapi import FastAPI

from messenger.sockets import sio
from messenger.fastApi import app

PORT = 8000

# deactivate monitoring task in python-socketio to avoid errores during shutdown
sio.eio.start_service_task = False


class UvicornTestServer(uvicorn.Server):
    """Uvicorn test server

    Usage:
        @pytest.fixture
        async def start_stop_server():
            server = UvicornTestServer()
            await server.up()
            yield
            await server.down()
    """

    def __init__(
        self,
        fast_api_app: FastAPI = app,
        host: str = "127.0.0.1",
        port: int = PORT,
    ):
        """Create a Uvicorn test server

        Args:
            app (FastAPI, optional): the FastAPI app. Defaults to main.app.
            host (str, optional): the host ip. Defaults to '127.0.0.1'.
            port (int, optional): the port. Defaults to PORT.
        """
        self._startup_done = asyncio.Event()
        self._serve_task = asyncio.create_task(self.serve())
        super().__init__(
            config=uvicorn.Config(fast_api_app, host=host, port=port)
        )

    async def startup(self, sockets: Optional[List] = None) -> None:
        """Override uvicorn startup"""
        await super().startup(sockets=sockets)
        self.config.setup_event_loop()
        self._startup_done.set()

    async def up(self) -> None:
        """Start up server asynchronously"""
        await self._startup_done.wait()

    async def down(self) -> None:
        """Shut down server asynchronously"""
        self.should_exit = True
        await self._serve_task


@pytest.fixture
async def startup_and_shutdown_server():
    """Start server as test fixture and tear down after test"""
    server = UvicornTestServer()
    await server.up()
    yield
    await server.down()
