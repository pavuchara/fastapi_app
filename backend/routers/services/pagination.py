"""
Работа с пагинацией.

Где:
    - CustomPage: "Обертка" схемы для добавления в схему параметров пагинации.
    - MyParams: query параметры пагинации.
    - MyPage: класс пагинации.

Исходный пакет пагинации:
    - https://uriyyo-fastapi-pagination.netlify.app/

Пример использования:
    @router.get("/", response_model=CustomPage[UserRetriveSchema], status_code=status.HTTP_200_OK)
    async def get_all_users(
        db: Annotated[AsyncSession, Depends(get_db)],
        request: Request,
        params: MyParams = Depends(),
    ):
        users_query = select(User)
        return await MyPage.create(users_query, db=db, params=params, request=request)
"""


from math import ceil
from urllib.parse import urlencode
from typing import Optional

from fastapi import Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_pagination import Page
from fastapi_pagination.bases import AbstractParams, RawParams

from fastapi_pagination.customization import (
    UseParams,
    CustomizedPage,
    UseExcludedFields,
    UseFieldsAliases,
)


class MyParams(BaseModel, AbstractParams):
    """Query параметры запроса для пагинации."""
    page: int = Query(1, ge=1, description="Page number")
    limit: int = Query(10, ge=1, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.limit if self.limit is not None else None,
            offset=(
                self.limit * (self.page - 1) if self.page is not None
                and self.limit is not None else None
            ),
        )


class MyPage(Page):
    """Реализация работы с постраничной разбивкой."""
    next: Optional[str]
    previous: Optional[str]

    @classmethod
    async def create(   # type: ignore
        cls,
        query,
        db: AsyncSession,
        params: MyParams,
        request: Request,
    ) -> "MyPage":
        total = await db.scalar(select(func.count()).select_from(query.subquery()))

        items_query = query.limit(params.limit).offset(params.to_raw_params().offset)
        items = await db.scalars(items_query)

        size = params.limit
        page = params.page
        total_pages = ceil(total / size) if total else 1

        base_url = str(request.url).split('?')[0]
        query_params = dict(request.query_params)

        # Следующая страница:
        if page < total_pages:
            query_params.update({"page": str(page + 1), "limit": str(size)})
            next_url = f"{base_url}?{urlencode(query_params)}"
        else:
            next_url = None

        # Предыдущая страница:
        if page > 1:
            query_params.update({"page": str(page - 1), "limit": str(size)})
            previous_url = f"{base_url}?{urlencode(query_params)}"
        else:
            previous_url = None

        return cls(
            total=total,
            items=items.all(),
            next=next_url,
            previous=previous_url,
            page=page,
            size=size,
        )


# Кастомизация вывда страницы.
CustomPage = CustomizedPage[
    MyPage,
    UseParams(MyParams),
    UseFieldsAliases(
        total="count",
        items="results",
    ),
    UseExcludedFields("page", "pages", "size"),
]
