from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from models.user import User
from models.core import Tag, Ingredient
from models.recipe import Recipe, RecipeTag, RecipeIngredient
from schemas.recipe import (
    RecipeCreateSchema,
    RecipeRetrieveSchema,
)
from routers.services.pagination import (
    MyPage,
    MyParams,
    CustomPage,
)
from routers.services.utils import get_object_or_404
from routers.services.security import current_user


router = APIRouter(prefix="/recipes", tags=["Recipe"])


@router.get("/")
async def get_all_recipes():
    pass


@router.post(
    "/",
    response_model=RecipeRetrieveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe(
    recipe_data: RecipeCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    tags = [
        (await get_object_or_404(db, Tag, Tag.id == request_tag_id))
        for request_tag_id in recipe_data.tags
    ]
    [
        await get_object_or_404(db, Ingredient, Ingredient.id == request_ingredient_id.id)
        for request_ingredient_id in recipe_data.ingredients
    ]
    recipe = Recipe(
        author_id=request_user.id,
        name=recipe_data.name,
        image=recipe_data.image,
        text=recipe_data.text,
        cooking_time=recipe_data.cooking_time,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)

    await db.scalars(
        insert(RecipeTag).returning(RecipeTag),
        [
            {
                "recipe_id": recipe.id,
                "tag_id": tag.id,
            }
            for tag in tags
        ]
    )
    await db.commit()
    added_ingredients = await db.scalars(
        insert(RecipeIngredient).returning(RecipeIngredient),
        [
            {
                "recipe_id": recipe.id,
                "ingredient_id": request_ingredient.id,
                "amount": request_ingredient.amount,
            }
            for request_ingredient in recipe_data.ingredients
        ]
    )
    await db.commit()

    added_ingredients_new = await db.scalars(
        select(RecipeIngredient)
        .where(RecipeIngredient.recipe_id == recipe.id)
        .options(
            selectinload(RecipeIngredient.ingredient)
        )
    )

    some_list = []
    for added_ingredient in added_ingredients_new:
        some_list.append(
            {
                "id": added_ingredient.ingredient_id,
                "name": added_ingredient.ingredient.name,
                "measurement_unit": added_ingredient.ingredient.measurement_unit,
                "amount": added_ingredient.amount,


            }
        )

    return {
        **recipe.__dict__,
        "author": request_user.__dict__,
        "tags": [tag.__dict__ for tag in tags],
        "ingredients": some_list,
    }


@router.get("/{recope_id}")
async def get_recipe():
    pass


@router.patch("/{recipe_id}")
async def update_recipe():
    pass


@router.delete("/{recipe_id}")
async def delete_recipe():
    pass


@router.get("/{recipe_id}/get-link/")
async def get_recipe_short_link():
    pass
