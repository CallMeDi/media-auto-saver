# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import asyncio

# 中文: 创建异步数据库引擎
# English: Create an asynchronous database engine
# connect_args={"check_same_thread": False} 是 SQLite 特有的参数, 允许多个线程访问同一个连接 (FastAPI 在后台线程池中运行路由)
# connect_args={"check_same_thread": False} is specific to SQLite, allowing multiple threads to access the same connection (FastAPI runs routes in a background thread pool)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # 中文: 设置为 True 可以打印 SQL 语句 (用于调试) / English: Set to True to print SQL statements (for debugging)
    future=True, # 中文: 使用 SQLAlchemy 2.0 风格 / English: Use SQLAlchemy 2.0 style
    connect_args={"check_same_thread": False}
)

# 中文: 创建异步会话工厂
# English: Create an asynchronous session factory
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False  # 中文: 防止在提交后访问对象时需要重新查询 / English: Prevent needing to re-query objects after commit
)

async def get_async_session() -> AsyncSession:
    """
    中文: FastAPI 依赖项, 用于获取异步数据库会话。
    English: FastAPI dependency to get an asynchronous database session.
    """
    async with AsyncSessionFactory() as session:
        yield session

async def init_db():
    """
    中文: 初始化数据库, 创建所有定义的表。
    English: Initialize the database, creating all defined tables.
    """
    async with async_engine.begin() as conn:
        # 中文: 删除所有现有表 (谨慎在生产环境中使用!)
        # English: Drop all existing tables (use with caution in production!)
        # await conn.run_sync(SQLModel.metadata.drop_all)
        # 中文: 创建所有在 SQLModel.metadata 中注册的表
        # English: Create all tables registered in SQLModel.metadata
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database initialized.")

# --- 同步引擎和会话 (如果某些操作需要同步执行, 例如 Alembic 迁移) ---
# --- Synchronous engine and session (if some operations need synchronous execution, e.g., Alembic migrations) ---
# sync_engine = create_engine(
#     settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"), # 使用同步驱动 / Use synchronous driver
#     echo=False,
#     future=True,
#     connect_args={"check_same_thread": False}
# )
# SyncSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# def get_sync_session() -> Session:
#     """
#     中文: 获取同步数据库会话的依赖项。
#     English: Dependency to get a synchronous database session.
#     """
#     with SyncSessionFactory() as session:
#         yield session

if __name__ == "__main__":
    # 中文: 作为一个脚本运行时, 初始化数据库
    # English: When run as a script, initialize the database
    async def main():
        await init_db()
    asyncio.run(main())
