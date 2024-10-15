from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from models.user import User, UserSubscription
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


@router.get("/", response_model=CustomPage[RecipeRetrieveSchema], status_code=status.HTTP_200_OK)
async def get_all_recipes(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagnination_query_params: Annotated[MyParams, Depends()],
    request: Request,
    request_user: Annotated[User, Depends(current_user)],
):
    query = (
        select(Recipe)
        .options(
            selectinload(Recipe.author),
            selectinload(Recipe.tags).joinedload(RecipeTag.tag),
            selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient),
        )
    )
    paginated_data = await MyPage.create(
        query, db=db, params=pagnination_query_params, request=request
    )

    items = []
    for recipe in paginated_data.items:
        data = {**recipe.__dict__}
        following = await db.scalar(
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
        items.append(data)
    paginated_data.items = items
    return CustomPage(**paginated_data.__dict__)


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
    tags = await db.scalars(select(Tag).where(Tag.id.in_(recipe_data.tags)))
    ingredients = await db.scalars(
        select(Ingredient)
        .where(Ingredient.id.in_([ingredient.id for ingredient in recipe_data.ingredients]))
    )
    tags_instances = tags.all()
    ingredients_instances = ingredients.all()

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

    recipe_tags = [RecipeTag(recipe_id=recipe.id, tag_id=tag.id) for tag in tags_instances]
    db.add_all(recipe_tags)
    await db.commit()

    added_ingredients = [
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
    db.add_all(added_ingredients)
    await db.commit()

    return {
        **recipe.__dict__,
        "author": request_user.__dict__,
        "tags": [tag.__dict__ for tag in tags],
        "ingredients": [
            {
                "id": ingredient.id,
                "name": ingredient.name,
                "measurement_unit": ingredient.measurement_unit,
                "amount": next(i.amount for i in recipe_data.ingredients if i.id == ingredient.id),
            }
            for ingredient in ingredients_instances
        ],
    }


@router.get("/{recope_id}")
async def get_recipe():
    pass


@router.patch("/{recipe_id}")
async def update_recipe():
    pass


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    if recipe.author_id == request_user.id:
        await db.delete(recipe)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Доступно только автору",
    )


@router.get("/{recipe_id}/get-link/")
async def get_recipe_short_link():
    pass
