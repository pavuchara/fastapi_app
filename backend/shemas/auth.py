from pydantic import BaseModel


class AuthGetTokenShcema(BaseModel):
    email: str
    password: str


class AuthRetrieveTokenSchema(BaseModel):
    auth_token: str
