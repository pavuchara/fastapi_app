from math import ceil
from typing import TypeVar, Sequence, Optional, Any

from fastapi import Query
from pydantic import BaseModel

from fastapi_pagination import Page
from fastapi_pagination.utils import create_pydantic_model
from fastapi_pagination.bases import AbstractParams, RawParams

from fastapi_pagination.customization import (
    UseParams,
    CustomizedPage,
    UseExcludedFields,
    UseFieldsAliases,
)


T = TypeVar("T")


class MyParams(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="Page number")
    limit: int = Query(50, ge=1, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.limit if self.limit is not None else None,
            offset=self.limit * (self.page - 1) if self.page is not None and self.limit is not None else None,
        )


class MyPage(Page):

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: MyParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> "MyPage":
        size = params.limit if params.limit is not None else (total or None)
        page = params.page if params.page is not None else 1

        if size in {0, None}:
            pages = 0
        elif total is not None:
            pages = ceil(total / size)
        else:
            pages = None

        return create_pydantic_model(
            cls,
            total=total,
            items=items,
            page=page,
            size=size,
            pages=pages,
            **kwargs,
        )




CustomPage = CustomizedPage[
    MyPage[T],
    UseParams(MyParams),
    UseFieldsAliases(
        total="count",
    ),
    UseExcludedFields("page", "pages", "size"),
]
