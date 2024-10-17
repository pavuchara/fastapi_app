from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.core import Ingredient, Tag
from models.user import (
    User,
    UserSubscription,
    UserFavorites,
    UserShoppingList,
)
from models.recipe import (
    Recipe,
    RecipeTag,
    RecipeIngredient,
)
from schemas.recipe import RecipeCreateSchema


class RecipeResponseDataPreparer:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_related_query_list(self):
        query = (
            select(Recipe)
            .options(
                selectinload(Recipe.author),
                selectinload(Recipe.tags).joinedload(RecipeTag.tag),
                selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient),
            )
        )
        return query

    async def get_related_data_from_instance(
        self,
        recipe: Recipe,
        request_user: User,
    ) -> dict[str, Any]:
        data = {**recipe.__dict__}
        following = await self.db.scalar(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == request_user.id,
                UserSubscription.following_id == recipe.author.id,
            )
        )
        data.update(
            {
                "author": {
                    **recipe.author.__dict__,
                    "is_subscribed": bool(following),
                }
            }
        )
        ingredients = await self.db.scalars(
            select(Ingredient)
            .where(Ingredient.id.in_([ing.ingredient_id for ing in recipe.ingredients]))
        )
        response_ingredients = [
            {
                "id": ingredient.id,
                "name": ingredient.name,
                "measurement_unit": ingredient.measurement_unit,
                "amount": next(
                    ing.amount for ing in recipe.ingredients
                    if ing.ingredient_id == ingredient.id
                ),
            }
            for ingredient in ingredients.all()
        ]
        data.update({"ingredients": response_ingredients})
        data.update({"tags": recipe.tag_list})
        is_favorited = await self.db.scalar(
            select(UserFavorites)
            .where(
                UserFavorites.user_id == request_user.id,
                UserFavorites.recipe_id == recipe.id,
            )
        )
        is_in_shopping_cart = await self.db.scalar(
            select(UserShoppingList)
            .where(
                UserShoppingList.user_id == request_user.id,
                UserShoppingList.recipe_id == recipe.id,
            )
        )
        data.update({"is_favorited": bool(is_favorited)})
        data.update({"is_in_shopping_cart": bool(is_in_shopping_cart)})
        return data

    async def get_related_inctance_by_id(self, recipe_id: int) -> Recipe | None:
        recipe = await self.db.scalar(
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(
                selectinload(Recipe.author),
                selectinload(Recipe.tags).joinedload(RecipeTag.tag),
                selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient),
            )
        )
        return recipe


class RecipeUpdator:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_recipe_with_related_fields(
        self,
        recipe: Recipe,
        recipe_data: RecipeCreateSchema,
    ) -> Recipe:
        tags = await self.db.scalars(select(Tag).where(Tag.id.in_(recipe_data.tags)))
        ingredients = await self.db.scalars(
            select(Ingredient)
            .where(Ingredient.id.in_([ingredient.id for ingredient in recipe_data.ingredients]))
        )
        tags_instances = tags.all()
        ingredients_instances = ingredients.all()

        await self._delete_relation_objects(recipe)
        await self.db.refresh(recipe)

        recipe.name = recipe_data.name
        recipe.image = recipe_data.image  # type: ignore
        recipe.text = recipe_data.text
        recipe.cooking_time = recipe_data.cooking_time
        self.db.add(recipe)
        await self.db.commit()

        new_recipe_tags = [RecipeTag(recipe_id=recipe.id, tag_id=tag.id) for tag in tags_instances]
        self.db.add_all(new_recipe_tags)
        await self.db.commit()

        new_recipe_ingredients = [
            RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                amount=next(
                    request_ingredient.amount for request_ingredient in recipe_data.ingredients
                    if request_ingredient.id == ingredient.id
                )
            )
            for ingredient in ingredients_instances
        ]
        self.db.add_all(new_recipe_ingredients)
        await self.db.commit()
        await self.db.refresh(recipe)
        return recipe

    async def _delete_relation_objects(self, recipe: Recipe) -> None:
        await self.db.execute(delete(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
        await self.db.execute(
            delete(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe.id)
        )
        await self.db.commit()
