# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import select, Session, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Type, TypeVar, Generic, Any, Dict

from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from .crud_link import CRUDBase # 导入通用的 CRUDBase / Import the generic CRUDBase

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    中文: User 模型的特定 CRUD 操作。
    English: Specific CRUD operations for the User model.
    """

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        中文: 通过用户名获取用户。
        English: Get a user by username.
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    # async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
    #     """
    #     中文: 通过邮箱获取用户。
    #     English: Get a user by email.
    #     """
    #     if not email: # 邮箱可能为 None / Email can be None
    #         return None
    #     result = await db.execute(select(User).where(User.email == email))
    #     return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        中文: 创建新用户, 密码会被哈希处理。
        English: Create a new user, password will be hashed.
        """
        # 中文: 使用 Pydantic 模型的 model_dump 方法将输入数据转换为字典, 排除密码
        # English: Use Pydantic model's model_dump method to convert input data to a dictionary, excluding password
        obj_in_data = obj_in.model_dump(exclude={"password"})
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(**obj_in_data, hashed_password=hashed_password)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate | Dict[str, Any]
    ) -> User:
        """
        中文: 更新用户信息, 如果提供了新密码, 会进行哈希处理。
        English: Update user information, if a new password is provided, it will be hashed.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # 中文: 如果更新数据中包含密码, 则哈希新密码
        # English: If the update data includes a password, hash the new password
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"] # 从更新数据中移除明文密码 / Remove plain password from update data
            update_data["hashed_password"] = hashed_password # 添加哈希后的密码 / Add hashed password

        # 中文: 调用基类的 update 方法处理其他字段
        # English: Call the base class's update method to handle other fields
        return await super().update(db=db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, db: AsyncSession, *, username: str, password: str
    ) -> Optional[User]:
        """
        中文: 通过用户名和密码验证用户。
        English: Authenticate a user by username and password.
        """
        user = await self.get_by_username(db=db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """
        中文: 检查用户是否处于活动状态。
        English: Check if the user is active.
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        中文: 检查用户是否为超级用户。
        English: Check if the user is a superuser.
        """
        return user.is_superuser

# 中文: 创建 User CRUD 操作的实例
# English: Create an instance of the User CRUD operations
user = CRUDUser(User)
