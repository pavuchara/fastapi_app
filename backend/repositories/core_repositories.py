from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.core import Ingredient, Tag
from schemas.core import (
    TagCreateSchema,
    IngredientCreateSchema,
)


class TagRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_tag(self, tag_data: TagCreateSchema) -> Tag:
        tag = Tag(
            name=tag_data.name,
            slug=tag_data.slug,
        )
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def get_all_tags(self) -> Sequence[Tag]:
        tags = await self.db.scalars(select(Tag))
        return tags.all()


class IngredientRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ingredient(self, ingredient_data: IngredientCreateSchema) -> Ingredient:
        ingredient = Ingredient(
            name=ingredient_data.name,
            measurement_unit=ingredient_data.measurement_unit,
        )
        self.db.add(ingredient)
        await self.db.commit()
        await self.db.refresh(ingredient)
        return ingredient

    async def get_all_ibgredients(
        self,
        request_query_params: str | None = None
    ) -> Sequence[Ingredient]:
        if request_query_params:
            ingredients = await self.db.scalars(
                select(Ingredient)
                .where(Ingredient.name.contains(request_query_params))
            )
        else:
            ingredients = await self.db.scalars(select(Ingredient))
        return ingredients.all()
