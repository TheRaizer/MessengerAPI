from fastapi import FastAPI

from .messages import router as messages
from .routers import users, auth, group_chat
from .friends import router as friends

app = FastAPI()

# routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(group_chat.router)
