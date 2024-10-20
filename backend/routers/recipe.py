from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
    Response,
    Request,
    status,
    Path
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from models.user import User
from models.recipe import Recipe
from schemas.recipe import (
    RecipeFilters,
    RecipeCreateSchema,
    RecipeRetrieveSchema,
    RecipeSimpleRetriveSchema,
)
from routers.services.pagination import (
    MyPage,
    MyParams,
    CustomPage,
)
from repositories.recipe_repositories import RecipeRepository
from repositories.user_repositories import (
    UserFavoritesRepository,
    UserShoppingListRepository,
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
    filters: RecipeFilters = Depends(),
    tags: Annotated[list[str] | None, Query()] = None
):
    recipe_repository = RecipeRepository(db)
    recipe_query = await recipe_repository.get_related_query_list(filters, tags, request_user)
    paginated_data = await MyPage.create(
        recipe_query, db=db, params=pagnination_query_params, request=request
    )

    items = []
    for recipe in paginated_data.items:
        data = await recipe_repository.to_schema_from_related_instance(recipe, request_user)
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
    recipe_repository = RecipeRepository(db)
    recipe = await recipe_repository.create_recipe(recipe_data, request_user)
    recipe_responce_data = (
        await recipe_repository.to_schema_from_related_instance(
            recipe,
            request_user,
        )
    )
    return recipe_responce_data


@router.get("/{recope_id}/", response_model=RecipeRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_recipe(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe_repository = RecipeRepository(db)
    recipe = await recipe_repository.get_related_instance_by_id(recipe_id)
    if recipe:
        response_data = (
            await recipe_repository.to_schema_from_related_instance(recipe, request_user)
        )
        return response_data
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Такого рецепта нет",
    )


@router.patch("/{recipe_id}/", response_model=RecipeRetrieveSchema, status_code=status.HTTP_200_OK)
async def update_recipe(
    recipe_id: Annotated[int, Path()],
    recipe_request_data: RecipeCreateSchema,
    request_user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    recipe_repository = RecipeRepository(db)
    request_recipe = await recipe_repository.get_related_instance_by_id(recipe_id)
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
    updated_recipe: Recipe = await recipe_repository.update_recipe_with_related_fields(
        request_recipe,
        recipe_request_data,
    )
    response_data = (
        await recipe_repository.to_schema_from_related_instance(updated_recipe, request_user)
    )
    return response_data


@router.delete("/{recipe_id}/")
async def delete_recipe(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe_repository = RecipeRepository(db)
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    if await recipe_repository.delete_recipe(recipe, request_user):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Доступно только автору",
    )


@router.post(
    "/{recipe_id}/shopping_cart/",
    response_model=RecipeSimpleRetriveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_to_shopping_cart(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    shopping_list_repository = UserShoppingListRepository(db)
    try:
        await shopping_list_repository.add_recipe_to_shopping_list(request_user, recipe)
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
    shopping_list_repository = UserShoppingListRepository(db)
    if await shopping_list_repository.delete_recipe_from_shopping_list(request_user, recipe):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/{recipe_id}/favorite/",
    response_model=RecipeSimpleRetriveSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_to_favorite(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    favorite_list_repository = UserFavoritesRepository(db)
    try:
        recipe = await favorite_list_repository.add_recipe_to_shopping_list(request_user, recipe)
        return recipe
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Уже в избранном",
        )


@router.delete("/{recipe_id}/favorite/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_from_favorites(
    recipe_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_user: Annotated[User, Depends(current_user)],
):
    recipe = await get_object_or_404(db, Recipe, Recipe.id == recipe_id)
    favorite_list_repository = UserFavoritesRepository(db)
    if await favorite_list_repository.delete_recipe_from_shopping_list(request_user, recipe):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# TODO Realize
@router.get("/{recipe_id}/get-link/")
async def get_recipe_short_link():
    pass
