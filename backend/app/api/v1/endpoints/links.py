# -*- coding: utf-8 -*-
# /usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any

from app import crud, models # 导入 models / Import models
from app.models.link import Link, LinkCreate, LinkRead, LinkUpdate, LinkType, LinkStatus
from app.db.session import get_async_session
from app.core.config import settings
from app.utils import extract_site_name
from app.api import deps # 导入认证依赖 / Import authentication dependencies
from app.tasks.link_monitor import process_link # 导入手动触发任务函数 / Import manual trigger task function
import asyncio # 导入 asyncio / Import asyncio

# 中文: 创建 API 路由器实例
# English: Create an API router instance
router = APIRouter()

@router.post("/", response_model=LinkRead, status_code=201, dependencies=[Depends(deps.get_current_active_user)])
async def create_link(
    *,
    db: AsyncSession = Depends(get_async_session),
    link_in: LinkCreate,
    # current_user: models.User = Depends(deps.get_current_active_user) # 获取当前用户 (如果需要与用户关联) / Get current user (if needed for association)
) -> Any:
    """
    中文: 创建一个新的链接。会自动尝试提取网站名称。
    English: Create a new link. Automatically attempts to extract the site name.
    """
    # 中文: 检查 URL 是否已存在
    # English: Check if the URL already exists
    existing_link = await crud.link.get_by_url(db=db, url=link_in.url)
    if existing_link:
        raise HTTPException(status_code=400, detail="Link with this URL already exists")

    # 中文: 尝试从 URL 提取网站名称
    # English: Try to extract the site name from the URL
    site_name = extract_site_name(link_in.url)
    link_in.site_name = site_name

    # 中文: 创建链接
    # English: Create the link
    link = await crud.link.create(db=db, obj_in=link_in)
    return link

@router.get("/", response_model=List[LinkRead], dependencies=[Depends(deps.get_current_active_user)])
async def read_links(
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    link_type: Optional[LinkType] = Query(None, description="按链接类型过滤 / Filter by link type"),
    site_name: Optional[str] = Query(None, description="按网站名称过滤 / Filter by site name"),
    status: Optional[LinkStatus] = Query(None, description="按状态过滤 (IDLE, MONITORING, DOWNLOADING, RECORDING, ERROR) / Filter by status (IDLE, MONITORING, DOWNLOADING, RECORDING, ERROR)"),
    is_enabled: Optional[bool] = Query(None, description="按是否启用过滤 / Filter by enabled status"),
    tags: Optional[str] = Query(None, description="按标签过滤 (包含任意一个即可) / Filter by tags (contains any)"),
    search: Optional[str] = Query(None, description="按名称或 URL 搜索 / Search by name or URL") # 添加搜索参数 / Add search parameter
) -> Any:
    """
    中文: 获取链接列表, 支持多种过滤条件、搜索和分页。
    English: Retrieve a list of links, supporting various filters, search, and pagination.
    """
    query = select(Link)

    # 应用过滤条件 / Apply filters
    if link_type:
        query = query.where(Link.link_type == link_type)
    if site_name:
        query = query.where(Link.site_name == site_name)
    if status:
        query = query.where(Link.status == status)
    if is_enabled is not None:
        query = query.where(Link.is_enabled == is_enabled)
    if tags:
        # 中文: 简单的标签过滤 (包含任意一个)
        # English: Simple tag filtering (contains any)
        tag_list = [tag.strip() for tag in tags.split(',')]
        # 使用 SQLite 的 regexp 函数进行标签过滤
        # Use SQLite's regexp function for tag filtering
        query = query.where(Link.tags.op('regexp')(f"({'|'.join(tag_list)})"))

    # 应用搜索条件 (按名称或 URL) / Apply search condition (by name or URL)
    if search:
        search_pattern = f"%{search}%" # 使用 LIKE 进行模糊匹配 / Use LIKE for fuzzy matching
        query = query.where(
            (Link.name.like(search_pattern)) |
            (Link.url.like(search_pattern))
        )

    # 应用分页 / Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    links = result.scalars().all()
    return links

@router.get("/{link_id}", response_model=LinkRead, dependencies=[Depends(deps.get_current_active_user)])
async def read_link(
    *,
    db: AsyncSession = Depends(get_async_session),
    link_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    中文: 通过 ID 获取单个链接。
    English: Get a single link by ID.
    """
    link = await crud.link.get(db=db, id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@router.put("/{link_id}", response_model=LinkRead, dependencies=[Depends(deps.get_current_active_user)])
async def update_link(
    *,
    db: AsyncSession = Depends(get_async_session),
    link_id: int,
    link_in: LinkUpdate,
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    中文: 更新一个链接。
    English: Update a link.
    """
    link = await crud.link.get(db=db, id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # 中文: 如果 URL 被更新, 检查新 URL 是否已存在
    # English: If the URL is updated, check if the new URL already exists
    if link_in.url and link_in.url != link.url:
        existing_link = await crud.link.get_by_url(db=db, url=link_in.url)
        if existing_link and existing_link.id != link_id:
            raise HTTPException(status_code=400, detail="Link with this new URL already exists")
        # 中文: 如果 URL 更新, 重新提取网站名称
        # English: If URL is updated, re-extract site name
        link_in_dict = link_in.model_dump(exclude_unset=True)
        link_in_dict["site_name"] = extract_site_name(link_in.url)
        link = await crud.link.update(db=db, db_obj=link, obj_in=link_in_dict)
    else:
        link = await crud.link.update(db=db, db_obj=link, obj_in=link_in)

    return link

@router.delete("/{link_id}", response_model=LinkRead, dependencies=[Depends(deps.get_current_active_user)])
async def delete_link(
    *,
    db: AsyncSession = Depends(get_async_session),
    link_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    中文: 删除一个链接。
    English: Delete a link.
    """
    link = await crud.link.get(db=db, id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # 中文: 删除关联的历史记录
    # English: Delete associated history logs
    deleted_history_count = await crud.history_log.remove_by_link(db=db, link_id=link_id)
    print(f"Deleted {deleted_history_count} history logs for link {link_id}") # Optional: log the count

    # 中文: 删除链接本身
    # English: Delete the link itself
    deleted_link = await crud.link.remove(db=db, id=link_id)

    return deleted_link # 返回被删除的对象 / Return the deleted object

@router.post("/{link_id}/trigger", dependencies=[Depends(deps.get_current_active_user)])
async def trigger_link_task(
    *,
    db: AsyncSession = Depends(get_async_session),
    link_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    中文: 手动触发单个链接的监控/下载任务。
    English: Manually trigger the monitoring/download task for a single link.
    """
    link = await crud.link.get(db=db, id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # 检查链接是否已在处理中 / Check if the link is already being processed
    if link.status in [models.link.LinkStatus.MONITORING, models.link.LinkStatus.DOWNLOADING, models.link.LinkStatus.RECORDING]:
         raise HTTPException(status_code=400, detail=f"Link {link_id} is already in status: {link.status}. Cannot trigger manually.")

    # 可以在这里选择性地将状态设置为 'queued' 或其他中间状态
    # Optionally set status to 'queued' or another intermediate status here
    # await crud.link.update_status(db=db, db_obj=link, status=models.link.LinkStatus.QUEUED)

    # 在后台启动任务 / Start the task in the background
    asyncio.create_task(process_link(link_id))

    return {"message": f"Task triggered for link {link_id}"}
