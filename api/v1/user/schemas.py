from pydantic import BaseModel


class UserUpdateRequest(BaseModel):
    name: str | None = None
