# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import select, Session, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Type, TypeVar, Generic, Any
from pydantic import BaseModel
from datetime import datetime

from app.models.history import HistoryLog, HistoryLogCreate, HistoryStatus
from .crud_link import CRUDBase # 导入通用的 CRUDBase / Import the generic CRUDBase

# 中文: 定义泛型类型变量 (虽然这里 UpdateSchemaType 未使用, 但保持 CRUDBase 结构一致)
# English: Define generic type variables (although UpdateSchemaType is unused here, keep CRUDBase structure consistent)
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel) # 未使用 / Unused

class CRUDHistoryLog(CRUDBase[HistoryLog, HistoryLogCreate, BaseModel]): # 使用 BaseModel 作为 UpdateSchemaType 占位符 / Use BaseModel as placeholder for UpdateSchemaType
    """
    中文: HistoryLog 模型的特定 CRUD 操作。
    English: Specific CRUD operations for the HistoryLog model.
    """

    async def create_log(
        self,
        db: AsyncSession,
        *,
        link_id: int,
        status: HistoryStatus,
        downloaded_files: Optional[List[str]] = None,
        error_message: Optional[str] = None,
        details: Optional[dict] = None
    ) -> HistoryLog:
        """
        中文: 创建一条新的历史记录。
        English: Create a new history log entry.
        """
        log_entry = HistoryLogCreate(
            link_id=link_id,
            status=status,
            downloaded_files=downloaded_files,
            error_message=error_message,
            details=details
            # timestamp 会自动生成 / timestamp will be generated automatically
        )
        return await self.create(db=db, obj_in=log_entry)

    async def get_multi_by_link(
        self, db: AsyncSession, *, link_id: int, skip: int = 0, limit: int = 100
    ) -> List[HistoryLog]:
        """
        中文: 获取特定链接的历史记录 (支持分页)。
        English: Get history logs for a specific link (with pagination support).
        """
        result = await db.execute(
            select(self.model)
            .where(self.model.link_id == link_id)
            .order_by(self.model.timestamp.desc()) # 按时间倒序 / Order by time descending
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def remove_by_link(self, db: AsyncSession, *, link_id: int) -> int:
        """
        中文: 删除特定链接的所有历史记录。
        English: Remove all history logs for a specific link.

        返回: 删除的记录数量。
        Returns: The number of deleted records.
        """
        # 注意: SQLModel 目前不直接支持批量删除的 delete() 方法返回计数。
        # Note: SQLModel currently doesn't directly support returning count from bulk delete().
        # 我们需要先查询再删除, 或者使用 SQLAlchemy Core API。这里采用先查询。
        # We need to query first then delete, or use SQLAlchemy Core API. Here we query first.

        logs_to_delete = await self.get_multi_by_link(db=db, link_id=link_id, limit=-1) # 获取所有 / Get all
        count = 0
        if logs_to_delete:
            for log in logs_to_delete:
                await db.delete(log)
                count += 1
            await db.commit()
        return count

# 中文: 创建 HistoryLog CRUD 操作的实例
# English: Create an instance of the HistoryLog CRUD operations
history_log = CRUDHistoryLog(HistoryLog)
