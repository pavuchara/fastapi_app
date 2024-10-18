from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from models.user import (
    User,
    UserFavorites,
    UserShoppingList,
)
from models.recipe import Recipe


class UserShoppingListRepository:

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
