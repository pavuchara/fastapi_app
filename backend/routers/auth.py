from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from models.user import User
from shemas.auth import (
    AuthGetTokenShcema,
    AuthRetriveTokenSchema,
)
from routers.services.security import (
    AuthToken,
    current_user,
    verify_password,
)


router = APIRouter(prefix="/auth/token", tags=["Auth"])


@router.post(
    "/login",
    response_model=AuthRetriveTokenSchema,
    status_code=status.HTTP_200_OK,
)
async def get_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_data: AuthGetTokenShcema,
):
    user = await db.scalar(
        select(User)
        .where(User.email == user_data.email)
        .options(
            selectinload(User.token)
        )
    )

    if user and verify_password(user_data.password, user.password):
        token = await AuthToken.get_token(db, user)
        return {"auth_token": token}
    raise HTTPException(
        detail="Пароль/почта введены неверно или такого пользователя нет",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.post(
    "/logaut",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(current_user)],
):
    print(current_user.token)
    await db.delete(current_user.token)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
