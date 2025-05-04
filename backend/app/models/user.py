# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone # 导入 timezone / Import timezone

class UserBase(SQLModel):
    """
    中文: 用户模型的基础字段
    English: Base fields for the User model
    """
    username: str = Field(unique=True, index=True, description="用户名 / Username")
    email: Optional[str] = Field(default=None, unique=True, index=True, description="邮箱 / Email")
    full_name: Optional[str] = Field(default=None, description="全名 / Full name")
    is_active: bool = Field(default=True, description="用户是否激活 / Is the user active")
    is_superuser: bool = Field(default=False, description="是否为超级用户 / Is superuser")

class User(UserBase, table=True):
    """
    中文: 用户数据库表模型
    English: User database table model
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(description="哈希后的密码 / Hashed password")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间 / Creation time")

class UserCreate(UserBase):
    """
    中文: 创建用户时使用的 Pydantic 模型 (需要密码)
    English: Pydantic model used when creating a user (requires password)
    """
    password: str # 创建时必须提供密码 / Password is required on creation

class UserRead(UserBase):
    """
    中文: 读取用户时使用的 Pydantic 模型 (不包含密码)
    English: Pydantic model used when reading a user (excludes password)
    """
    id: int
    created_at: datetime

class UserUpdate(SQLModel):
    """
    中文: 更新用户时使用的 Pydantic 模型 (所有字段可选)
    English: Pydantic model used when updating a user (all fields optional)
    """
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None # 允许更新密码 / Allow updating password
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
