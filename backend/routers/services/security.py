import secrets
from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext

from alchemy.db_depends import get_db
from models.user import User, UserBaseToken


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def crypt_password(password: str) -> str:
    return bcrypt_context.hash(password)


def verify_password(input_password: str, having_password: str):
    return bcrypt_context.verify(input_password, having_password)


class TokenAuthScheme(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        return credentials


# TODO интерфейс?
class AuthToken:

    @classmethod
    async def get_token(cls, db: AsyncSession, user: User) -> str:
        if user.token and user.token.token:
            return user.token.token
        token = await cls.__create_token(db, user)
        return token

    @classmethod
    async def __create_token(cls, db: AsyncSession, user: User) -> str:
        generated_token = await cls.__generate_token()
        token = UserBaseToken(
            token=generated_token,
            user_id=user.id,
        )
        db.add(token)
        await db.commit()
        return generated_token

    @classmethod
    async def __generate_token(cls) -> str:
        return secrets.token_hex(32)

    @classmethod
    async def get_user_from_token(
        cls,
        db: Annotated[AsyncSession, Depends(get_db)],
        token: Annotated[HTTPAuthorizationCredentials, Depends(TokenAuthScheme())],
    ) -> User | None:
        request_token = token.credentials[len("Token "):]
        db_token = await db.scalar(
            select(UserBaseToken)
            .where(UserBaseToken.token == request_token)
            .options(
                selectinload(UserBaseToken.user)
            )
        )

        if db_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен",
            )

        return db_token.user

    @classmethod
    async def authenticate_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str,

    ) -> User | None:
        user = await db.scalar(
            select(User)
            .where(User.email == email)
        )
        if not user or not bcrypt_context.verify(password, user.password):
            return None
        return user
