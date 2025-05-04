# -*- coding: utf-8 -*-
# /usr/bin/env python3

import logging
from typing import Any, Optional
from datetime import datetime # 导入 datetime / Import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models
from app.api import deps
from app.core.config import settings
from app.core import security # 导入 security 模块 / Import security module

logger = logging.getLogger(__name__)
router = APIRouter()

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="密码重置令牌 / Password reset token")
    new_password: str = Field(..., min_length=8, description="新密码 (至少8位) / New password (at least 8 characters)")

class GenerateResetTokenResponse(BaseModel):
    username: str
    reset_token: str
    expires_at: datetime

# --- 端点实现 / Endpoint Implementations ---

@router.post("/password-recovery/{username}", response_model=GenerateResetTokenResponse, status_code=status.HTTP_201_CREATED)
async def recover_password_generate_token(
    username: str,
    db: AsyncSession = Depends(deps.get_async_session),
    # current_user: models.User = Depends(deps.get_current_active_superuser) # 限制只有管理员能生成令牌 / Restrict token generation to superusers
) -> Any:
    """
    中文: 为指定用户生成密码重置令牌 (需要安全传递给用户)。
    English: Generate a password reset token for a specific user (needs secure delivery to the user).

    注意: 当前实现允许任何人调用此接口为任意用户生成令牌。
          在生产环境中, 应添加权限控制 (例如仅限管理员)。
    Note: Current implementation allows anyone to call this for any user.
          In production, add permission control (e.g., superuser only).
    """
    user = await crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )

    # 中文: 创建并存储重置令牌
    # English: Create and store the reset token
    reset_token_obj = await crud.password_reset_token.create_reset_token(db, user_id=user.id)
    logger.info(f"Password reset token generated for user {username}: {reset_token_obj.token}")

    # 中文: 返回令牌信息 (在实际应用中, 不应直接返回令牌, 而是通过其他方式传递)
    # English: Return token info (in real apps, token shouldn't be returned directly, but delivered otherwise)
    return GenerateResetTokenResponse(
        username=user.username,
        reset_token=reset_token_obj.token,
        expires_at=reset_token_obj.expires_at
    )


@router.post("/reset-password/", status_code=status.HTTP_200_OK)
async def reset_password(
    *,
    db: AsyncSession = Depends(deps.get_async_session),
    body: ResetPasswordRequest = Body(...)
) -> Any:
    """
    中文: 使用有效的重置令牌重置密码。
    English: Reset password using a valid reset token.
    """
    token = body.token
    new_password = body.new_password

    # 中文: 查找令牌
    # English: Find the token
    token_obj = await crud.password_reset_token.get_by_token(db, token=token)
    if not token_obj:
        raise HTTPException(status_code=400, detail="Invalid password reset token")

    # 中文: 验证令牌是否有效 (未过期且未使用)
    # English: Validate the token (not expired and not used)
    if not crud.password_reset_token.is_token_valid(token_obj):
         raise HTTPException(status_code=400, detail="Password reset token is invalid or has expired")

    # 中文: 获取关联的用户
    # English: Get the associated user
    user = await crud.user.get(db, id=token_obj.user_id)
    if not user:
        # 中文: 这种情况理论上不应发生, 但以防万一
        # English: This shouldn't happen theoretically, but just in case
        raise HTTPException(status_code=404, detail="User associated with token not found")

    # 中文: 更新用户密码
    # English: Update user password
    hashed_password = security.get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)

    # 中文: 将令牌标记为已使用
    # English: Mark the token as used
    await crud.password_reset_token.use_token(db, token_obj=token_obj)

    await db.commit()
    logger.info(f"Password successfully reset for user {user.username}")
    return {"message": "Password updated successfully"}
