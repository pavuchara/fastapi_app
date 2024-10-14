import secrets
from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext

from alchemy.db_depends import get_db
from models.user import User, UserBaseToken


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def crypt_password(password: str) -> str:
    return bcrypt_context.hash(password)


def verify_password(input_password: str, having_password: str) -> bool:
    return bcrypt_context.verify(input_password, having_password)


class TokenAuthScheme(HTTPBearer):

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """
        Схема токена не определяется, достаточно просто получить валидный payload.
        """
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme:
            credentials = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
            return credentials
        raise HTTPException(
            detail="Invalid authentication credentials",
            status_code=status.HTTP_403_FORBIDDEN,
        )


# TODO интерфейс?
class AuthToken:
    """
    Реализация работы аутентификации с токеном.
    """

    @classmethod
    async def get_token(cls, db: AsyncSession, user: User) -> str:
        """Получение токена."""
        if user.token and user.token.token:
            return user.token.token
        token = await cls.__create_token(db, user)
        return token

    @classmethod
    async def get_user_from_token(
        cls,
        db: Annotated[AsyncSession, Depends(get_db)],
        token: Annotated[HTTPAuthorizationCredentials, Depends(TokenAuthScheme())],
    ) -> User | None:
        """Получение пользователя по предоставленному токену."""
        request_token = token.credentials
        user = await db.scalar(
            select(User)
            .join(User.token)
            .options(selectinload(User.token))
            .where(UserBaseToken.token == request_token)
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Необходима аутентификация",
            )

        return user

    @classmethod
    async def __create_token(cls, db: AsyncSession, user: User) -> str:
        """Создание токена в бд."""
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
        """Генерация токена."""
        return secrets.token_hex(32)


async def current_user(user: Annotated[User, Depends(AuthToken.get_user_from_token)]):
    """Просто текущий пользователь."""
    return user
