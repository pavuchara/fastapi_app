from pydantic import BaseModel


class AuthGetTokenSchema(BaseModel):
    email: str
    password: str


class AuthRetrieveTokenSchema(BaseModel):
    auth_token: str
