import logging
from shed_soft_user.dao.base_model import Base
# Импортируем модели, чтобы они зарегистрировались в Base.metadata
from shed_soft_user.dao.models import User, Note, Realm  # noqa: F401

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from shed_soft_user.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST_USER}:{settings.DB_PORT_USER}/{settings.DB_NAME_USER}"

engine = create_async_engine(DATABASE_URL, pool_size=settings.POOL_SIZE_USER, max_overflow=settings.MAX_OVERFLOW_USER)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Инициализирует базу данных, создавая все таблицы"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def dispose_db():
    """Закрывает все соединения с БД"""
    await engine.dispose()
    logger.info("Database connections closed")
