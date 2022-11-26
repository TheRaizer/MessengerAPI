from fastapi import FastAPI
from .routers import users, auth, messages, friends, group_chat

app = FastAPI()

# routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(group_chat.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
