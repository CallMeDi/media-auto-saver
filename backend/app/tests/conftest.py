# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Dict, Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# 中文: 导入主应用和配置
# English: Import main application and settings
# 注意: 这里的导入路径假设 pytest 是从 backend 目录运行的
# Note: Import paths assume pytest is run from the backend directory
from app.main import app
from app.core.config import settings
from app.db.session import get_async_session # 导入原始的 session 依赖 / Import original session dependency

# --- 测试数据库设置 / Test Database Setup ---
# 中文: 使用内存中的 SQLite 数据库进行测试, 避免影响主数据库
# English: Use an in-memory SQLite database for tests to avoid affecting the main DB
# 注意: 内存数据库在每次测试运行后都会清空
# Note: In-memory database is cleared after each test run
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True, connect_args={"check_same_thread": False})
TestSessionFactory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    中文: 覆盖 FastAPI 的数据库会话依赖, 使用测试数据库会话。
    English: Override FastAPI's database session dependency to use the test database session.
    """
    async with TestSessionFactory() as session:
        yield session

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """
    中文: 在测试会话开始时创建测试数据库表, 结束后删除。
    English: Create test database tables at the start of the test session and drop them afterwards.
    Also creates the initial superuser in the test database.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 中文: 在测试数据库中创建初始用户
    # English: Create initial user in the test database
    async with TestSessionFactory() as session:
        from app import crud, models # 导入 CRUD 和模型 / Import CRUD and models
        initial_username = "admin"
        initial_password = "changeme"
        initial_email = "admin@test.com" # 使用测试邮箱 / Use test email

        user = await crud.user.get_by_username(session, username=initial_username)
        if not user:
            user_in = models.UserCreate(
                username=initial_username,
                password=initial_password,
                email=initial_email,
                is_superuser=True,
                is_active=True
            )
            await crud.user.create(session, obj_in=user_in)
            print(f"\nINFO: Created initial superuser '{initial_username}' in test database.") # 打印信息以便确认 / Print info for confirmation
        else:
            print(f"\nINFO: Initial superuser '{initial_username}' already exists in test database.")


    yield
    # 测试结束后不需要显式删除内存数据库 / No need to explicitly drop in-memory DB after tests

# --- 覆盖应用依赖 / Override App Dependencies ---
app.dependency_overrides[get_async_session] = override_get_async_session

# --- 测试客户端 Fixture / Test Client Fixture ---
@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    中文: 提供一个用于发送 API 请求的异步 HTTP 客户端。
    English: Provide an async HTTP client for sending API requests.
    """
    # 使用 ASGI transport 直接与 FastAPI 应用交互 / Use ASGI transport to interact directly with the FastAPI app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as c:
        yield c

# --- 认证辅助 Fixtures / Authentication Helper Fixtures ---
@pytest.fixture(scope="module")
def test_username() -> str:
    return "testuser"

@pytest.fixture(scope="module")
def test_password() -> str:
    return "testpassword"

@pytest_asyncio.fixture(scope="module")
async def test_user(client: httpx.AsyncClient, test_username: str, test_password: str) -> Dict[str, Any]:
    """
    中文: 创建一个用于测试的普通用户。
    English: Create a regular user for testing.
    """
    # 注意: 由于注册端点已移除, 我们需要找到其他方式创建用户,
    # 或者暂时跳过需要普通用户的测试, 先测试管理员。
    # Note: Since registration endpoint is removed, we need another way to create users,
    # or skip tests requiring regular users for now and test admin first.
    # 这里我们假设有一个创建用户的 API (需要先实现) 或直接操作数据库
    # Here we assume a user creation API exists (needs implementation) or direct DB manipulation
    # 暂时返回空字典 / Return empty dict for now
    # TODO: Implement user creation for tests
    from app import crud, models # Import here to avoid circular dependencies at module level

    async with TestSessionFactory() as session:
        user = await crud.user.get_by_username(session, username=test_username)
        if not user:
            user_in_create = models.UserCreate(
                username=test_username,
                password=test_password,
                email=f"{test_username}@example.com",
                is_superuser=False,
                is_active=True
            )
            user = await crud.user.create(session, obj_in=user_in_create)
        # Ensure the returned object is suitable for attribute access (e.g., user.username)
        # If crud.user.create returns a Pydantic model, it's fine.
        # If it's a dict, ensure keys match expected access patterns.
        # For consistency and to ensure it's a User model instance:
        return await crud.user.get_by_username(session, username=test_username)


@pytest_asyncio.fixture(scope="module")
async def superuser_token_headers(client: httpx.AsyncClient) -> Dict[str, str]:
    """
    中文: 获取初始超级用户 (admin) 的认证令牌 Headers。
    English: Get authentication token headers for the initial superuser (admin).
    """
    login_data = {
        "username": "admin", # 使用 main.py 中创建的初始用户 / Use initial user created in main.py
        "password": "changeme", # 使用默认密码 / Use default password
    }
    # 中文: 明确发送 x-www-form-urlencoded 数据
    # English: Explicitly send x-www-form-urlencoded data
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data, headers=headers)
    r.raise_for_status() # 确保登录成功 / Ensure login is successful
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers

@pytest_asyncio.fixture(scope="module")
async def normal_user_token_headers(client: httpx.AsyncClient, test_user: Dict[str, Any], test_password: str) -> Dict[str, str]:
    """
    中文: 获取普通测试用户的认证令牌 Headers。
    English: Get authentication token headers for a regular test user.
    """
    # login_data = {
    #     "username": test_user["username"],
    login_data = {
        "username": test_user.username, # Get username from the test_user object
        "password": test_password,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"} # Ensure correct content type
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data, headers=headers)
    r.raise_for_status() # Ensure login is successful (e.g. status 200)
    tokens = r.json()
    a_token = tokens["access_token"]
    auth_headers = {"Authorization": f"Bearer {a_token}"}
    return auth_headers
