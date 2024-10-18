from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db_depends import get_db
from models.user import User
from models.core import Tag, Ingredient
from schemas.core import (
    TagCreateSchema,
    TagRetrieveSchema,
    IngredientCreateSchema,
    IngredientRetrieveSchema,
)
from repositories.core_repositories import (
    TagRepository,
    IngredientRepository,
)
from routers.services.utils import get_object_or_404
from routers.services.security import current_user


router = APIRouter(tags=["Core"])


@router.post("/tags", response_model=TagRetrieveSchema, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(current_user)],
):
    tag_repository = TagRepository(db)
    return await tag_repository.create_tag(tag_data)


@router.get(
    "/tags",
    response_model=list[TagRetrieveSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tag_repository = TagRepository(db)
    return await tag_repository.get_all_tags()


@router.get("/tags/{tag_id}", response_model=TagRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_tag(
    tag_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_object_or_404(db, Tag, Tag.id == tag_id)


@router.post(
    "/ingredients",
    response_model=IngredientRetrieveSchema,
    status_code=status.HTTP_200_OK,
)
async def create_ingredient(
    ingredient_data: IngredientCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(current_user)],
):
    ingredient_repository = IngredientRepository(db)
    return await ingredient_repository.create_ingredient(ingredient_data)


@router.get(
    "/ingredients",
    response_model=list[IngredientRetrieveSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_ingredients(
    db: Annotated[AsyncSession, Depends(get_db)],
    request_query_params: Annotated[str | None, Query()] = None,
):
    ingredient_repository = IngredientRepository(db)
    return await ingredient_repository.get_all_ibgredients(request_query_params)


@router.get(
    "/ingredients/{ingredient_id}",
    response_model=IngredientRetrieveSchema,
    status_code=status.HTTP_200_OK,
)
async def get_ingredient(
    ingredient_id: Annotated[int, Path()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_object_or_404(db, Ingredient, Ingredient.id == ingredient_id)
