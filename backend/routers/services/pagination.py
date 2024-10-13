from math import ceil
from typing import TypeVar, Sequence, Optional, Any

from fastapi import Query, Request
from pydantic import BaseModel

from fastapi_pagination import Page
from fastapi_pagination.bases import AbstractParams, RawParams
from fastapi_pagination.links import LimitOffsetPage

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
            offset=(
                self.limit * (self.page - 1) if self.page is not None
                and self.limit is not None else None
            ),
        )


class MyPage(Page):
    next: Optional[str]
    previous: Optional[str]
    page: Optional[int] = None
    size: Optional[int] = None

    @classmethod
    def create(   # type: ignore
        cls,
        items: Sequence[T],
        params: MyParams,
        request: Request,
    ) -> "MyPage":
        total = len(items)
        size = params.limit if params.limit is not None else (total or None)
        page = params.page if params.page is not None else 1
        print("1" * 100)
        print(total)
        print()
        print("1" * 100)

        if size in {0, None}:
            pages = 0
        elif total is not None:
            pages = ceil(total / size)
        else:
            pages = None

        base_url = str(request.url).split('?')[0]

        next_url = (
            f"{base_url}?page={page + 1}&limit={size}"
            if page < pages else None
        )
        previous_url = (
            f"{base_url}?page={page - 1}&limit={size}"
            if page > 1 else None
        )

        return cls(
            total=total,
            items=items,
            next=next_url,
            previous=previous_url,
            # **kwargs
        )


CustomPage = CustomizedPage[
    MyPage[T],
    UseParams(MyParams),
    UseFieldsAliases(
        total="count",
    ),
    UseExcludedFields("page", "pages", "size"),
]
