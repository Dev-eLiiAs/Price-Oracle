from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool: Celery tasks each run their own asyncio.run() (a fresh event loop
# per task), and asyncpg connections are bound to the loop that created them.
# A pooled connection reused across loops raises "another operation in
# progress". NullPool opens a fresh connection per checkout instead.
engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
