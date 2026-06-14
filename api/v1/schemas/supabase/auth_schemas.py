from pydantic import BaseModel


class EmailSignUp(BaseModel):
    email: str
    password: str


class EmailSignIn(BaseModel):
    email: str
    password: str
