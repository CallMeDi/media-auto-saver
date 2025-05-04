# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import select, Session, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timezone

from app.models.password_reset import PasswordResetToken, PasswordResetTokenCreate, generate_reset_token, calculate_expiry_date
from .crud_link import CRUDBase # 导入通用的 CRUDBase / Import the generic CRUDBase

class CRUDPasswordResetToken(CRUDBase[PasswordResetToken, PasswordResetTokenCreate, SQLModel]): # UpdateSchema 未使用 / UpdateSchema unused
    """
    中文: PasswordResetToken 模型的特定 CRUD 操作。
    English: Specific CRUD operations for the PasswordResetToken model.
    """

    async def create_reset_token(self, db: AsyncSession, *, user_id: int) -> PasswordResetToken:
        """
        中文: 为用户创建并存储一个新的密码重置令牌。
        English: Create and store a new password reset token for a user.
        """
        token = generate_reset_token()
        expires_at = calculate_expiry_date()
        token_obj = PasswordResetToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            used=False
        )
        db.add(token_obj)
        await db.commit()
        await db.refresh(token_obj)
        return token_obj

    async def get_by_token(self, db: AsyncSession, *, token: str) -> Optional[PasswordResetToken]:
        """
        中文: 通过令牌字符串获取令牌对象。
        English: Get a token object by its token string.
        """
        result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == token))
        return result.scalars().first()

    async def use_token(self, db: AsyncSession, *, token_obj: PasswordResetToken) -> PasswordResetToken:
        """
        中文: 将令牌标记为已使用。
        English: Mark a token as used.
        """
        token_obj.used = True
        token_obj.expires_at = datetime.now(timezone.utc) # 使其立即过期, 使用 aware datetime / Make it expire immediately, use aware datetime
        db.add(token_obj)
        await db.commit()
        await db.refresh(token_obj)
        return token_obj

    def is_token_valid(self, token_obj: PasswordResetToken) -> bool:
        """
        中文: 检查令牌是否有效 (未过期且未使用)。
        English: Check if a token is valid (not expired and not used).
        """
        now_utc = datetime.now(timezone.utc)
        expires_at_aware = token_obj.expires_at
        # 中文: 如果从数据库读取的 expires_at 是 naive 的, 附加 UTC 时区
        # English: If expires_at read from DB is naive, make it aware (assume UTC)
        if expires_at_aware.tzinfo is None:
            expires_at_aware = expires_at_aware.replace(tzinfo=timezone.utc)

        return not token_obj.used and expires_at_aware > now_utc

# 中文: 创建 PasswordResetToken CRUD 操作的实例
# English: Create an instance of the PasswordResetToken CRUD operations
password_reset_token = CRUDPasswordResetToken(PasswordResetToken)
