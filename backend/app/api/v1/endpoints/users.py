# -*- coding: utf-8 -*-
# /usr/bin/env python3

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Body, status # 导入 Body, status / Import Body, status
from pydantic import BaseModel, Field # 导入 BaseModel, Field / Import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models
from app.api import deps
from app.core import security # 导入 security / Import security

router = APIRouter()

class UpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

@router.get("/me", response_model=models.UserRead)
async def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    中文: 获取当前用户信息。
    English: Get current user information.
    """
    return current_user

@router.put("/me/password", status_code=status.HTTP_200_OK)
async def update_password_me(
    *,
    db: AsyncSession = Depends(deps.get_async_session),
    body: UpdatePassword = Body(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    中文: 更新当前用户的密码。
    English: Update current user's password.
    """
    # 验证当前密码是否正确 / Verify current password
    if not security.verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    # 更新密码 / Update password
    await crud.user.update(db, db_obj=current_user, obj_in={"password": body.new_password})
    return {"message": "Password updated successfully"}

# TODO: 添加获取用户列表 (管理员) / Add get users list (admin)
# TODO: 添加更新用户信息 (管理员/自己, 非密码部分) / Add update user info (admin/self, non-password part)
# TODO: 添加删除用户 (管理员) / Add delete user (admin)
