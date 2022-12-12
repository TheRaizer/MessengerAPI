from pydantic import BaseModel


class RequesterAddressee(BaseModel):
    requester_id: int
    addressee_id: int
