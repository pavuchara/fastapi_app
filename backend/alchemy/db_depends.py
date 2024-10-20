from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from alchemy.db import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Генератор асингхронной сессии, при возникновении ошибок, транзакция роллбекается."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
