from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    status,
    Request,
)
from alchemy.db_depends import get_db
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shemas.user import (
    UserCreationSchema,
    UserRetriveSchema,
)
from models.user import User
from routers.services.validators import validate_user_exist
from routers.services.pagination import CustomPage, MyPage, MyParams
from routers.services.utils import get_object_or_404
from routers.services.security import (
    current_user,
    crypt_password,
)


router = APIRouter(prefix="/users", tags=["User"])


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


@router.get("/", response_model=CustomPage[UserRetriveSchema], status_code=status.HTTP_200_OK)
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    params: MyParams = Depends(),
):
    users_query = select(User)
    return await MyPage.create(users_query, db=db, params=params, request=request)


@router.get("/me", response_model=UserRetriveSchema, status_code=status.HTTP_200_OK)
async def get_current_user(
    current_user: Annotated[User, Depends(current_user)]
):
    return current_user


@router.get("/{user_id}", response_model=UserRetriveSchema, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(current_user)],
):
    user = await get_object_or_404(db, User, User.id == user_id)
    return user
