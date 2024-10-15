from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.core import Ingredient
from models.user import (
    User,
    UserSubscription,
)
from models.recipe import (
    Recipe,
    RecipeTag,
    RecipeIngredient,
)


class RecipeDataPreparer:

    def __init__(self, db: AsyncSession, recipe_id: int):
        self.db = db
        self.recipe_id = recipe_id

    async def get_related_query(self):
        query = (
            select(Recipe)
            .options(
                selectinload(Recipe.author),
                selectinload(Recipe.tags).joinedload(RecipeTag.tag),
                selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient),
            )
        )
        return query

    async def get_related_data_from_instance(self, recipe: Recipe, request_user: User):
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
                **recipe.author.__dict__,
                "is_subscribed": bool(following),
            }
        )
        ingredients = await db.scalars(
            select(Ingredient)
            .where(Ingredient.id.in_([ing.id for ing in recipe.ingredients]))
        )
        response_ingredients = [
            {
                "id": ingredient.id,
                "name": ingredient.name,
                "measure_unit": ingredient.measurement_unit,
                "amount": next(
                    ing.amount for ing in recipe.ingredients
                    if ing.ingredient_id == ingredient.id
                ),
            }
            for ingredient in ingredients.all()
        ]
        data.update({"ingredients": response_ingredients})
        data.update({"tags": [recipe_tag.tag for recipe_tag in recipe.tags]})
        return data
