from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from shemas.user import (
    UserCreationSchema,
    UserRetriveSchema,
)
from models.user import User
from routers.services.security import AuthToken
from routers.services.validators import validate_user_exist
from routers.services.security import crypt_password


router = APIRouter(prefix="/users")


@router.post("/", response_model=UserRetriveSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreationSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await validate_user_exist(db, user_email=user_data.email, username=user_data.username)
    user = User(
        email=user_data.email,
        username=user_data.username,
        password=crypt_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserRetriveSchema, status_code=status.HTTP_200_OK)
async def get_current_user(
    user: Annotated[User, Depends(AuthToken.get_user_from_token)]
):
    return user
