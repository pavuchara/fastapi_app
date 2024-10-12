from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def validate_user_exist(
    db: AsyncSession,
    user_email: str,
    username: str,
) -> None:
    user = await db.scalar(
        select(User)
        .where(
            or_(
                User.email == user_email,
                User.username == username,
            )
        )
    )
    if user:
        raise HTTPException(
            detail="Пользователь с таким email | username уже есть",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
