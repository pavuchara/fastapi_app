from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Request,
    status,
    Path
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from models.user import User, UserShoppingList, UserFavorites
from models.core import Tag, Ingredient
from models.recipe import Recipe, RecipeTag, RecipeIngredient
from schemas.recipe import (
    RecipeCreateSchema,
    RecipeRetrieveSchema,
    RecipeSimpleRetriveSchema,
)
from routers.services.pagination import (
    MyPage,
    MyParams,
    CustomPage,
)
from models.services.queries import (
    RecipeResponseDataPreparer,
    RecipeUpdator,
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
    recipe_data_preparer = RecipeResponseDataPreparer(db)
    recipe_query = await recipe_data_preparer.get_related_query_list()
    paginated_data = await MyPage.create(
        recipe_query, db=db, params=pagnination_query_params, request=request
    )

    items = []
    for recipe in paginated_data.items:
        data = await recipe_data_preparer.get_related_data_from_instance(recipe, request_user)
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


@router.get("/{recope_id}", response_model=RecipeRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_recipe(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe_data_preparer = RecipeResponseDataPreparer(db)
    recipe = await recipe_data_preparer.get_related_inctance_by_id(recipe_id)
    if recipe:
        response_data = (
            await recipe_data_preparer.get_related_data_from_instance(recipe, request_user)
        )
        return response_data
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Такого рецепта нет",
    )


@router.patch("/{recipe_id}", response_model=RecipeRetrieveSchema, status_code=status.HTTP_200_OK)
async def update_recipe(
    recipe_id: Annotated[int, Path()],
    recipe_request_data: RecipeCreateSchema,
    request_user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    recipe_data_preparer = RecipeResponseDataPreparer(db)
    request_recipe = await recipe_data_preparer.get_related_inctance_by_id(recipe_id)
    if not request_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нет такого рецепта.",
        )
    if request_recipe and request_recipe.author != request_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только для автора.",
        )
    recipe_updator = RecipeUpdator(db)
    updated_recipe: Recipe = (
        await recipe_updator.update_recipe_with_related_fields(request_recipe, recipe_request_data)
    )
    response_data = (
        await recipe_data_preparer.get_related_data_from_instance(updated_recipe, request_user)
    )
    return response_data


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: Annotated[int, Path()],
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


@router.post(
    "/{recipe_id}/shopping_cart",
    response_model=RecipeSimpleRetriveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_to_shopping_cart(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    shopping_list = UserShoppingList(
        user_id=request_user.id,
        recipe_id=recipe.id,
    )
    try:
        db.add(shopping_list)
        await db.commit()
        return recipe
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Уже в корзине",
        )


@router.delete("/{recipe_id}/shopping_cart/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_from_shopping_cart(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    shopping_list = await db.scalar(
        select(UserShoppingList)
        .where(
            UserShoppingList.user_id == request_user.id,
            UserShoppingList.recipe_id == recipe.id,
        )
    )
    if shopping_list:
        await db.delete(shopping_list)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/{recipe_id}/favorite",
    response_model=RecipeSimpleRetriveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_to_favorite(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    favorite_list = UserFavorites(
        user_id=request_user.id,
        recipe_id=recipe.id,
    )
    try:
        db.add(favorite_list)
        await db.commit()
        return recipe
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Уже в избранном",
        )


@router.delete("/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_from_favorites(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    favorite_list = await db.scalar(
        select(UserFavorites)
        .where(
            UserFavorites.user_id == request_user.id,
            UserFavorites.recipe_id == recipe.id
        )
    )
    if favorite_list:
        await db.delete(favorite_list)
        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/{recipe_id}/get-link/")
async def get_recipe_short_link():
    pass
