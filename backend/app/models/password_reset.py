# -*- coding: utf-8 -*-
# /usr/bin/env python3

import secrets
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, DateTime # 导入 Column 和 DateTime / Import Column and DateTime

from app.core.config import settings # 用于获取令牌过期时间 / To get token expiration time

# 中文: 定义密码重置令牌的默认过期时间 (例如: 1 小时)
# English: Define default expiration time for password reset tokens (e.g., 1 hour)
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1

class PasswordResetTokenBase(SQLModel):
    """
    中文: 密码重置令牌的基础字段
    English: Base fields for the PasswordResetToken model
    """
    token: str = Field(unique=True, index=True, description="重置令牌 / Reset token")
    user_id: int = Field(foreign_key="user.id", index=True, description="关联的用户 ID / Associated User ID")
    # 中文: 明确指定数据库列类型为带时区的 DateTime
    # English: Explicitly specify the database column type as DateTime with timezone
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)), description="令牌过期时间 / Token expiration time")
    used: bool = Field(default=False, description="令牌是否已被使用 / Whether the token has been used")

class PasswordResetToken(PasswordResetTokenBase, table=True):
    """
    中文: 密码重置令牌数据库表模型
    English: PasswordResetToken database table model
    """
    id: Optional[int] = Field(default=None, primary_key=True)

class PasswordResetTokenCreate(SQLModel):
    """
    中文: 创建密码重置令牌时使用的模型 (只需要 user_id)
    English: Model used when creating a password reset token (only needs user_id)
    """
    user_id: int

def generate_reset_token() -> str:
    """
    中文: 生成一个安全的随机令牌字符串。
    English: Generate a secure random token string.
    """
    return secrets.token_urlsafe(32)

def calculate_expiry_date() -> datetime:
    """
    中文: 计算令牌的过期时间。
    English: Calculate the token's expiration time.
    """
    return datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS) # 确保返回 aware datetime / Ensure aware datetime is returned
