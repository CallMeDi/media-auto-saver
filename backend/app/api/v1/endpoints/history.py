# -*- coding: utf-8 -*-
# /usr/bin/env python3

import logging # 导入 logging / Import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select # 导入 select / Import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any

from app import crud, models # 导入 models / Import models
from app.models.history import HistoryLog, HistoryLogRead # 导入 HistoryLog 模型 / Import HistoryLog model
from app.db.session import get_async_session
from app.api import deps # 导入认证依赖 / Import authentication dependencies

# 中文: 获取日志记录器
# English: Get logger
logger = logging.getLogger(__name__)

# 中文: 创建 API 路由器实例
# English: Create an API router instance
router = APIRouter()

@router.get("/", response_model=List[HistoryLogRead], dependencies=[Depends(deps.get_current_active_user)])
async def read_history_logs(
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    link_id: Optional[int] = Query(None, description="按关联的链接 ID 过滤 / Filter by associated link ID"),
    status: Optional[str] = Query(None, description="按状态过滤 (success 或 failed) / Filter by status (success or failed)") # 添加状态过滤参数 / Add status filter parameter
) -> Any:
    """
    中文: 获取历史记录列表, 支持按 link_id、status 过滤和分页。
    English: Retrieve a list of history logs, supporting filtering by link_id, status, and pagination.
    """
    query = select(HistoryLog)

    # 应用过滤条件 / Apply filters
    if link_id is not None:
        query = query.where(HistoryLog.link_id == link_id)
    if status is not None:
        # 确保状态是有效的 (虽然前端下拉框限制了, 后端也应验证)
        # Ensure status is valid (frontend dropdown limits, but backend should also validate)
        valid_statuses = ["success", "failed"] # 根据 HistoryLog 模型中的实际状态调整 / Adjust based on actual statuses in HistoryLog model
        if status.lower() in valid_statuses:
            query = query.where(HistoryLog.status == status.lower())
        else:
            # 可以选择忽略无效状态或返回错误 / Can choose to ignore invalid status or return error
            # 这里选择忽略 / Choosing to ignore here
            logger.warning(f"Received invalid status filter: {status}")


    # 应用排序 (按时间倒序) / Apply sorting (by time descending)
    query = query.order_by(HistoryLog.timestamp.desc())

    # 应用分页 / Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    history = result.scalars().all()

    return history

@router.delete("/{history_id}", response_model=HistoryLogRead, dependencies=[Depends(deps.get_current_active_user)])
async def delete_history_log(
    *,
    db: AsyncSession = Depends(get_async_session),
    history_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    中文: 删除单条历史记录。
    English: Delete a single history log entry.
    """
    history = await crud.history_log.get(db=db, id=history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History log not found")
    deleted_history = await crud.history_log.remove(db=db, id=history_id)
    return deleted_history

@router.delete("/by_link/{link_id}", response_model=dict, dependencies=[Depends(deps.get_current_active_user)])
async def delete_history_logs_by_link(
    *,
    db: AsyncSession = Depends(get_async_session),
    link_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    中文: 删除特定链接的所有历史记录。
    English: Delete all history logs for a specific link.
    """
    # 中文: 检查链接是否存在 (可选, 但更友好)
    # English: Check if the link exists (optional, but friendlier)
    link = await crud.link.get(db=db, id=link_id)
    if not link:
         raise HTTPException(status_code=404, detail=f"Link with id {link_id} not found")

    deleted_count = await crud.history_log.remove_by_link(db=db, link_id=link_id)
    return {"message": f"Successfully deleted {deleted_count} history logs for link_id {link_id}"}
