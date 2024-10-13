from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    Request,
    Response,
    HTTPException,
)
from alchemy.db_depends import get_db
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shemas.user import (
    UserCreationSchema,
    UserRetrieveSchema,
)
from models.user import User, UserSubscription
from routers.services.validators import validate_user_exist
from routers.services.pagination import CustomPage, MyPage, MyParams
from routers.services.utils import get_object_or_404
from routers.services.security import (
    current_user,
    crypt_password,
)


router = APIRouter(prefix="/users", tags=["User"])


@router.post("/", response_model=UserRetrieveSchema, status_code=status.HTTP_201_CREATED)
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


@router.get("/", response_model=CustomPage[UserRetrieveSchema], status_code=status.HTTP_200_OK)
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    params: Annotated[MyParams, Depends()],
):
    users_query = select(User)
    return await MyPage.create(users_query, db=db, params=params, request=request)


@router.get("/me", response_model=UserRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_current_user(
    current_user: Annotated[User, Depends(current_user)]
):
    return current_user


@router.get(
    "/subscriptions",
    response_model=CustomPage[UserRetrieveSchema],
    status_code=status.HTTP_200_OK,
)
async def get_user_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
    params: Annotated[MyParams, Depends()],
    request: Request,
):
    query = (
        select(User)
        .join(UserSubscription, UserSubscription.following_id == User.id)
        .where(UserSubscription.user_id == request_user.id)
    )
    return await MyPage.create(query, db=db, params=params, request=request)


@router.post(
    "/{user_id}/subscribe",
    response_model=UserRetrieveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)]
):
    subscribe_target = await get_object_or_404(db, User, User.id == user_id)
    try:
        subscription = UserSubscription(
            user_id=request_user.id,
            following_id=subscribe_target.id,
        )
        db.add(subscription)
        await db.commit()
        return subscribe_target
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Подписка на самого себя/дублирование подписки запрещено.",
        )


@router.delete("/{user_id}/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)]
):
    target_user = await get_object_or_404(db, User, User.id == user_id)
    following = await db.scalar(
        select(UserSubscription)
        .where(
            UserSubscription.user_id == request_user.id,
            UserSubscription.following_id == target_user.id,
        )
    )
    if following:
        await db.delete(following)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Вы не подписаны на этого пользователя",
    )


@router.get("/{user_id}", response_model=UserRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(current_user)],
):
    user = await get_object_or_404(db, User, User.id == user_id)
    return user
