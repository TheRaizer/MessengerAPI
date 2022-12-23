"""Initializes the FastAPI app."""

from fastapi import FastAPI, status
from .routers import users, auth, messages, friends, group_chat

app = FastAPI()

# routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(group_chat.router)


@app.get("/health", status_code=status.HTTP_200_OK)
def perform_healthcheck():
    return {"health": "Everything OK!"}
