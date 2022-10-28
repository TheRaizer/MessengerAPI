from fastapi import FastAPI
from .routers import users, auth, messages


app = FastAPI()

# routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(messages.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
