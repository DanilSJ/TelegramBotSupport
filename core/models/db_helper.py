from asyncio import current_task

from sqlalchemy import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)

from core.config import settings


class DatabaseHelper:
    def __init__(self, url: str, echo: bool = False, pool=AsyncAdaptedQueuePool):
        if settings.DB_POOL_NULL:
            pool = NullPool

        self.engine = create_async_engine(
            url=url,
            echo=echo,
            poolclass=pool,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def get_scoped_session(self):
        return async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )

    async def session_dependency(self) -> AsyncSession:
        """Обычная сессия с автоматическим закрытием"""
        async with self.session_factory() as session:
            yield session
            # Сессия автоматически закроется при выходе из контекста

    async def scoped_session_dependency(self) -> AsyncSession:
        """Scoped сессия с автоматическим закрытием"""
        scoped_session = self.get_scoped_session()
        session = scoped_session()
        try:
            yield session
        finally:
            await session.close()
            await scoped_session.remove()

    async def dispose(self):
        """Закрытие engine при завершении приложения"""
        await self.engine.dispose()


db_helper = DatabaseHelper(
    url=settings.db_url,
    echo=settings.DB_ECHO,
)
