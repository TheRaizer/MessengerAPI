from fastapi import APIRouter

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={404: {"description": "Not found"}},
)

@router.post('/')
def send_message():
    return