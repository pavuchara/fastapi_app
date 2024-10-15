from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from sqlalchemy import select
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
from routers.services.pagination import (
    MyPage,
    MyParams,
    CustomPage,
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
    tag = Tag(
        name=tag_data.name,
        slug=tag_data.slug,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get(
    "/tags",
    response_model=CustomPage[TagRetrieveSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    request_query_params: Annotated[MyParams, Depends()],
):
    query = select(Tag)
    return await MyPage.create(query, db=db, params=request_query_params, request=request)


@router.get("/tags/{tag_id}", response_model=TagRetrieveSchema, status_code=status.HTTP_200_OK)
async def get_tag(
    tag_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tag = await get_object_or_404(db, Tag, Tag.id == tag_id)
    return tag


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
    ingredient = Ingredient(
        name=ingredient_data.name,
        measurement_unit=ingredient_data.measurement_unit,
    )
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


@router.get(
    "/ingredients",
    response_model=CustomPage[IngredientRetrieveSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_ingredients(
    db: Annotated[AsyncSession, Depends(get_db)],
    request_query_params: Annotated[MyParams, Depends()],
    request: Request,
):
    query = select(Ingredient)
    return await MyPage.create(query, db=db, request=request, params=request_query_params)


@router.get(
    "/ingredients/{ingredient_id}",
    response_model=IngredientRetrieveSchema,
    status_code=status.HTTP_200_OK,
)
async def get_ingredient(
    ingredient_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ingredient = await get_object_or_404(db, Ingredient, Ingredient.id == ingredient_id)
    return ingredient