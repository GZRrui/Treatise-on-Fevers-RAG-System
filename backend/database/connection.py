"""
数据库连接管理
支持 SQLite/MySQL/PostgreSQL
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import logging

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# 全局变量
_engine = None
_session_factory = None


class Database:
    """
    数据库管理器

    统一管理数据库连接和会话。
    支持 SQLite、MySQL、PostgreSQL。
    """

    def __init__(self, database_url: str = None):
        """
        Args:
            database_url: 数据库连接 URL
        """
        self.database_url = database_url or DATABASE_URL
        self._engine = None
        self._session_factory = None

    def create_engine(self):
        """创建数据库引擎"""
        self._engine = create_async_engine(
            self.database_url,
            echo=False,  # 生产环境设为 False
            pool_size=10,
            max_overflow=20,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(f"数据库引擎创建完成: {self.database_url}")

    async def create_tables(self):
        """创建所有表"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")

    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            logger.info("数据库连接已关闭")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    用于 FastAPI 的Depends
    """
    global _engine, _session_factory

    if _engine is None:
        _engine = create_async_engine(DATABASE_URL, echo=False)
        _session_factory = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )

    async with _session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    from backend.database.models import Base

    global _engine, _session_factory

    _engine = create_async_engine(DATABASE_URL, echo=False)
    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )

    # 创建表
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("数据库初始化完成")


async def close_db():
    """关闭数据库"""
    global _engine

    if _engine:
        await _engine.dispose()
        logger.info("数据库连接已关闭")