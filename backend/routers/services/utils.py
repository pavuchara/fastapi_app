from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_object_or_404(db: AsyncSession, model, expression):
    request_object = await db.scalar(
        select(model)
        .where(expression)
    )
    if request_object:
        return request_object
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Страницы не существует."
    )
