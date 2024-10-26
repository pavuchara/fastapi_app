from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row

from models.user import (
    User,
    UserFavorites,
    UserShoppingList,
    UserSubscription,
)
from models.recipe import Recipe
from routers.services.security import crypt_password, verify_password
from schemas.user import (
    UserCreationSchema,
    UserAvatarSchema,
    UserPasswordChangeSchema,
)


class UserRepository:
    """Репозиторий работы с пользователями."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, user_data: UserCreationSchema) -> User:
        user = User(
            email=user_data.email,
            username=user_data.username,
            password=crypt_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(
        self,
        user_id: int,
        request_user: User,
    ) -> Row[tuple[User, bool]] | None:
        query = (
            select(
                User,
                case((UserSubscription.user_id.isnot(None), True), else_=False)
                .label("is_subscribed")
            )
            .outerjoin(
                UserSubscription,
                (User.id == UserSubscription.following_id)
                & (UserSubscription.user_id == request_user.id)
            )
            .options(selectinload(User.subscriptions))
            .where(User.id == user_id)
            .distinct()
        )
        user_q = await self.db.execute(query)
        return user_q.first()

    async def add_avatar(self, user: User, avatar_data: UserAvatarSchema) -> UserAvatarSchema:
        user.avatar = avatar_data.avatar
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return avatar_data

    async def delete_avatar(self, user: User) -> None:
        user.avatar = None
        self.db.add(user)
        await self.db.commit()

    async def change_user_password(
        self,
        user: User,
        password_data: UserPasswordChangeSchema,
    ) -> bool:
        if verify_password(password_data.current_password, user.password):
            user.password = crypt_password(password_data.new_password)
            self.db.add(user)
            await self.db.commit()
            return True
        return False

    async def get_total(self, query=None):
        if query:
            return await self.db.scalar(select(func.count()).select_from(query.subquery()))
        return await self.db.scalar(select(func.count()).select_from(User))

    async def get_all_instanses_limit_offset(self, request_user: User, limit: int, offset: int):
        query = (
            select(
                User,
                case((UserSubscription.user_id.isnot(None), True), else_=False)
                .label("is_subscribed")
            )
            .outerjoin(
                UserSubscription,
                (User.id == UserSubscription.following_id)
                & (UserSubscription.user_id == request_user.id)
            )
            .options(selectinload(User.subscriptions))
            .distinct()
            .limit(limit)
            .offset(offset)
        )
        all_users = await self.db.execute(query)
        return all_users.all()

    async def to_shema(
        self,
        query_result: Row[tuple[User, bool]] | list[Row[tuple[User, bool]]],
        many: bool = False,
    ):
        if many:
            users = [
                {**user.__dict__, "is_subscribed": is_subscribed}
                for user, is_subscribed in query_result
            ]
            return users
        return {**query_result[0].__dict__, "is_subscribed": query_result[1]}

    async def get_users_query_with_recipes(self, request_user: User):
        query = (
            select(User)
            .join(UserSubscription, UserSubscription.following_id == User.id)
            .where(UserSubscription.user_id == request_user.id)
            .options(
                selectinload(User.recipe),
            )
            .distinct()
        )
        return query


class UserShoppingListRepository:
    """Репозиторий работы со списком покупок пользователя."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_recipe_to_shopping_list(self, request_user: User, recipe: Recipe) -> Recipe:
        shopping_list = UserShoppingList(
            user_id=request_user.id,
            recipe_id=recipe.id,
        )
        self.db.add(shopping_list)
        await self.db.commit()
        return recipe

    async def delete_recipe_from_shopping_list(self, request_user: User, recipe: Recipe) -> bool:
        shopping_list = await self.db.scalar(
            select(UserShoppingList)
            .where(
                UserShoppingList.user_id == request_user.id,
                UserShoppingList.recipe_id == recipe.id,
            )
        )
        if shopping_list:
            await self.db.delete(shopping_list)
            await self.db.commit()
            return True
        return False


class UserFavoritesRepository:
    """Репозиторий работы со списком избранного."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_recipe_to_shopping_list(self, request_user: User, recipe: Recipe) -> Recipe:
        favorite_list = UserFavorites(
            user_id=request_user.id,
            recipe_id=recipe.id,
        )
        self.db.add(favorite_list)
        await self.db.commit()
        return recipe

    async def delete_recipe_from_shopping_list(self, request_user: User, recipe: Recipe) -> bool:
        favorite_list = await self.db.scalar(
            select(UserFavorites)
            .where(
                UserFavorites.user_id == request_user.id,
                UserFavorites.recipe_id == recipe.id
            )
        )
        if favorite_list:
            await self.db.delete(favorite_list)
            await self.db.commit()
            return True
        return False


class UserSubscriptionRepository:
    """Репозиторий работы с подписками."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def follow_user(self, request_user: User, target_user: User) -> None:
        subscription = UserSubscription(
            user_id=request_user.id,
            following_id=target_user.id,
        )
        self.db.add(subscription)
        await self.db.commit()

    async def unfollow(self, request_user: User, target_user: User) -> bool:
        following = await self.db.scalar(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == request_user.id,
                UserSubscription.following_id == target_user.id,
            )
        )
        if following:
            await self.db.delete(following)
            await self.db.commit()
            return True
        return False
