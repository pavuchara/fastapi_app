from pydantic import BaseModel


class AuthGetTokenShcema(BaseModel):
    email: str
    password: str


class AuthRetriveTokenSchema(BaseModel):
    auth_token: str
