# -*- coding: utf-8 -*-
# /usr/bin/env python3

from typing import Generator, Optional, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import get_async_session

# 中文: 定义 OAuth2 密码 Bearer 模式, 指定获取令牌的 URL (稍后创建)
# English: Define OAuth2 password Bearer scheme, specifying the token URL (to be created later)
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

async def get_current_user(
    db: AsyncSession = Depends(get_async_session), token: str = Depends(reusable_oauth2)
) -> models.User:
    """
    中文: FastAPI 依赖项, 用于获取当前已认证的用户。
    English: FastAPI dependency to get the current authenticated user.

    从请求头中获取 Bearer 令牌, 解码并验证, 然后从数据库中查找用户。
    Gets the Bearer token from the request header, decodes and validates it,
    then retrieves the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        if payload is None:
            raise credentials_exception
        token_data = schemas.TokenPayload(sub=payload)
    except JWTError:
        raise credentials_exception

    # 中文: 假设 subject (sub) 是用户 ID
    # English: Assume subject (sub) is the user ID
    try:
        user_id = int(token_data.sub)
    except (ValueError, TypeError):
         # 如果 sub 不是有效的整数 ID, 抛出异常
         # If sub is not a valid integer ID, raise exception
         raise credentials_exception

    user = await crud.user.get(db, id=user_id)
    if not user:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    中文: FastAPI 依赖项, 获取当前已认证且处于活动状态的用户。
    English: FastAPI dependency to get the current authenticated and active user.
    """
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """
    中文: FastAPI 依赖项, 获取当前已认证、活动且是超级用户的用户。
    English: FastAPI dependency to get the current authenticated, active, and superuser user.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
