from .database import AsyncSessionLocal
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generates Async Sessions to be used by other Functions
    :return: Session Object
    """
    async with AsyncSessionLocal() as session:
        yield session
