from fastapi import FastAPI
from .routers import users, auth, messages, group_chat
from .friends import router as friends

app = FastAPI()

# routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(group_chat.router)