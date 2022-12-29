# import asyncio
# from unittest.mock import MagicMock, patch
# import pytest

# import socketio


# @pytest.mark.asyncio
# @patch("messenger.sockets.user_status.get_friendlist_ids")
# async def test_status_change(
#     get_friendlist_ids_mock: MagicMock, startup_and_shutdown_server
# ):
#     # TODO: mock out jwt verification to always return true. actually idek
#     # get_friendlist_ids_mock.return_value =

#     sio = socketio.AsyncClient()
#     future = asyncio.get_running_loop().create_future()

#     @sio.on("status change")
#     def on_status_change(data):
#         print(f"Client received: {data}")
#         # set the result
#         future.set_result(data)

#     message = "Hello!"
#     await sio.connect(
#         f"http://localhost:{PORT}", socketio_path="/sio/socket.io/"
#     )
#     print(f"Client sends: {message}")
#     await sio.emit("chat message", message)
#     # wait for the result to be set (avoid waiting forever)
#     await asyncio.wait_for(future, timeout=1.0)
#     await sio.disconnect()
#     assert future.result() == message
