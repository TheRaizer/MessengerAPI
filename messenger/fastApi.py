"""Initializes the FastAPI app."""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from messenger.routers import users, auth, messages, friends, group_chat
from messenger.settings import origins
from messenger.sockets.socket import sio_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(group_chat.router)

app.mount("/ws", sio_app)


@app.get("/health", status_code=status.HTTP_200_OK)
def perform_healthcheck():
    return {"health": "Everything OK!"}
