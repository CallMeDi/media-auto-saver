# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
from typing import Dict
import httpx

from app.core.config import settings
from app.models import UserRead # 导入 UserRead 用于验证响应 / Import UserRead for response validation

@pytest.mark.asyncio
async def test_login_access_token(client: httpx.AsyncClient) -> None:
    """
    中文: 测试使用正确的凭证登录并获取令牌。
    English: Test logging in with correct credentials and getting a token.
    """
    login_data = {
        "username": "admin",
        "password": "changeme", # 使用默认密码 / Use default password
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_access_token_wrong_password(client: httpx.AsyncClient) -> None:
    """
    中文: 测试使用错误密码登录。
    English: Test logging in with the wrong password.
    """
    login_data = {
        "username": "admin",
        "password": "wrongpassword",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_login_access_token_wrong_username(client: httpx.AsyncClient) -> None:
    """
    中文: 测试使用错误用户名登录。
    English: Test logging in with the wrong username.
    """
    login_data = {
        "username": "wronguser",
            "password": "changeme",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_get_current_user(
    client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]
) -> None:
    """
    中文: 测试使用有效令牌获取当前用户信息。
    English: Test getting current user info with a valid token.
    """
    r = await client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    assert r.status_code == 200
    current_user = r.json()
    # 验证返回的数据结构符合 UserRead 模型 / Validate response against UserRead model
    assert UserRead.model_validate(current_user)
    assert current_user["username"] == "admin"
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is True

@pytest.mark.asyncio
async def test_get_current_user_no_token(client: httpx.AsyncClient) -> None:
    """
    中文: 测试在没有令牌的情况下获取当前用户信息。
    English: Test getting current user info without a token.
    """
    r = await client.get(f"{settings.API_V1_STR}/users/me")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: httpx.AsyncClient) -> None:
    """
    中文: 测试使用无效令牌获取当前用户信息。
    English: Test getting current user info with an invalid token.
    """
    headers = {"Authorization": "Bearer invalidtoken"}
    r = await client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 401
    assert r.json()["detail"] == "Could not validate credentials"
