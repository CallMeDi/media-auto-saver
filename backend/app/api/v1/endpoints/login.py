# -*- coding: utf-8 -*-
# /usr/bin/env python3

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Form # 导入 status 和 Form / Import status and Form
# from fastapi.security import OAuth2PasswordRequestForm # 不再使用 / No longer used
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()

@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_async_session),
    username: str = Form(...), # 直接接收表单字段 / Receive form fields directly
    password: str = Form(...)
) -> Any:
    """
    中文: 令牌登录端点, 获取访问令牌。
    English: Token login endpoint, get an access token.

    使用用户名和密码进行验证。
    Authenticates using username and password.
    """
    user = await crud.user.authenticate(
        db, username=username, password=password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    # 中文: 创建访问令牌
    # English: Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires # 使用用户 ID 作为 subject / Use user ID as subject
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/test-token", response_model=models.UserRead)
async def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    中文: 测试访问令牌是否有效。
    English: Test access token validity.
    """
    return current_user

# (移除了 register_new_user 端点 / Removed register_new_user endpoint)

# TODO: 添加获取当前用户信息端点 (移至 users.py) / Add endpoint to get current user info (moved to users.py)
# TODO: 移除用户管理端点 / Remove user management endpoints
