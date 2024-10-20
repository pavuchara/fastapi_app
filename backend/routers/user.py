from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    status,
    Request,
    Response,
    HTTPException,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from schemas.user import (
    UserCreationSchema,
    UserRetrieveSchema,
    UserPasswordChangeSchema,
    UserAvatarSchema,
    UserWithRecipesSchema,
)
from models.user import User
from repositories.user_repositories import (
    UserRepository,
    UserSubscriptionRepository,
)
from routers.services.validators import validate_user_exist
from routers.services.pagination import CustomPage, MyPage, MyParams
from routers.services.utils import get_object_or_404
from routers.services.security import current_user


router = APIRouter(prefix="/users", tags=["User"])


@router.post("/", response_model=UserRetrieveSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreationSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await validate_user_exist(db, user_email=user_data.email, username=user_data.username)
    user_repository = UserRepository(db)
    return await user_repository.create_user(user_data)


@router.get("/", response_model=CustomPage[UserRetrieveSchema], status_code=status.HTTP_200_OK)
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    params: Annotated[MyParams, Depends()],
    request_user: Annotated[User, Depends(current_user)],
):
    user_repository = UserRepository(db)
    paginated_data = await MyPage.create_with_repository(
        params=params,
        request=request,
        request_user=request_user,
        repository=user_repository,
    )
    return CustomPage(**paginated_data.__dict__)


@router.get("/me/", response_model=UserRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_current_user(
    current_user: Annotated[User, Depends(current_user)]
):
    return current_user


@router.put("/me/avatar/", response_model=UserAvatarSchema, status_code=status.HTTP_200_OK)
async def creaete_user_avatar(
    avatar_data: UserAvatarSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    user_repository = UserRepository(db)
    return await user_repository.add_avatar(request_user, avatar_data)


@router.delete("/me/avatar/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    user_repository = UserRepository(db)
    await user_repository.delete_avatar(request_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/set_password/", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(
    password_data: UserPasswordChangeSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    user_repository = UserRepository(db)
    if await user_repository.change_user_password(request_user, password_data.new_password):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        detail="Неверные данные",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.get(
    "/subscriptions/",
    response_model=CustomPage[UserWithRecipesSchema],
    status_code=status.HTTP_200_OK,
)
async def get_user_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
    params: Annotated[MyParams, Depends()],
    request: Request,
):
    user_repository = UserRepository(db)
    query = await user_repository.get_users_query_with_recipes(request_user)
    paginated_data = await MyPage.create(query, db=db, params=params, request=request)
    items = [
        {**user.__dict__, "is_subscribed": True, "recipes": user.recipe}
        for user in paginated_data.items
    ]
    paginated_data.items = items
    return CustomPage(**paginated_data.__dict__)


@router.post(
    "/{user_id}/subscribe/",
    response_model=UserRetrieveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe_user(
    user_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)]
):
    subscription_repository = UserSubscriptionRepository(db)
    target_user = await get_object_or_404(db, User, User.id == user_id)
    try:
        await subscription_repository.follow_user(request_user, target_user)
        return {
            **target_user.__dict__,
            "is_subscribed": True,
        }
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Подписка на самого себя/дублирование подписки запрещено.",
        )


@router.delete("/{user_id}/subscribe/", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_user(
    user_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)]
):
    subscription_repository = UserSubscriptionRepository(db)
    target_user = await get_object_or_404(db, User, User.id == user_id)
    if await subscription_repository.unfollow(request_user, target_user):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Вы не подписаны на этого пользователя",
    )


@router.get("/{user_id}/", response_model=UserRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    user_repository = UserRepository(db)
    user = await user_repository.get_user_by_id(user_id, request_user)
    if user:
        return await user_repository.to_shema(user)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Такого пользователя нет."
    )
