# -*- coding: utf-8 -*-
# /usr/bin/env python3

import asyncio
import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.models.link import Link, LinkStatus, LinkType
from app.models.history import HistoryStatus # 导入 HistoryStatus / Import HistoryStatus
from app.services.downloader import download_media
from app.db.session import AsyncSessionFactory
from app.core.config import settings # 修正导入路径 / Correct import path

# 中文: 获取日志记录器 (已在 main.py 中配置)
# English: Get logger (configured in main.py)
logger = logging.getLogger(__name__)

async def process_link(link_id: int):
    """
    中文: 处理单个链接的下载或录制任务。
    English: Process the download or recording task for a single link.

    这个函数将在后台任务中执行。
    This function will be executed in a background task.
    """
    logger.info(f"Starting processing for link_id: {link_id}")
    # 中文: 在后台任务中创建独立的数据库会话
    # English: Create an independent database session within the background task
    async with AsyncSessionFactory() as db:
        try:
            link = await crud.link.get(db=db, id=link_id)
            if not link or not link.is_enabled:
                logger.warning(f"Link {link_id} not found or disabled. Skipping.")
                return

            # 中文: 更新状态为下载中/录制中 (操作开始, 非成功状态)
            # English: Update status to downloading/recording (operation started, not a success state)
            current_action_status = LinkStatus.DOWNLOADING if link.link_type == LinkType.CREATOR else LinkStatus.RECORDING
            await crud.link.update_status(db=db, db_obj=link, status=current_action_status, is_success=False) # Indicate not a success yet
            logger.info(f"Link {link_id} status updated to {current_action_status}")

            # 中文: 调用下载服务
            # English: Call the download service
            download_result = await download_media(link)

            # 中文: 根据下载结果更新状态
            # 中文: 根据下载结果更新状态并记录历史
            # English: Update status and log history based on download result
            if download_result["status"] == "success":
                # 中文: 操作成功, 设置 is_success=True
                # English: Operation succeeded, set is_success=True
                await crud.link.update_status(db=db, db_obj=link, status=LinkStatus.IDLE, is_success=True)
                await crud.history_log.create_log(
                    db=db,
                    link_id=link_id,
                    status=HistoryStatus.SUCCESS,
                    downloaded_files=download_result.get("downloaded_files"),
                    # details=... # 可以添加文件大小等信息 / Can add file size etc.
                )
                logger.info(f"Link {link_id} processed successfully. Status set to IDLE. History logged.")
            else:
                error_msg = download_result.get("error", "Unknown download error")
                # 中文: 操作失败, is_success 默认为 False
                # English: Operation failed, is_success defaults to False
                await crud.link.update_status(db=db, db_obj=link, status=LinkStatus.ERROR, error_message=error_msg)
                await crud.history_log.create_log(
                    db=db,
                    link_id=link_id,
                    status=HistoryStatus.FAILURE,
                    error_message=error_msg
                )
                logger.error(f"Link {link_id} processing failed. Status set to ERROR. History logged. Error: {error_msg}")

        except Exception as e:
            logger.error(f"Error processing link {link_id}: {e}", exc_info=True)
            # 中文: 发生异常时也尝试更新状态为错误
            # English: Also try to update status to error when an exception occurs
            # 中文: 记录处理异常的历史
            # English: Log history for processing exception
            try:
                # 中文: 再次获取 link 对象, 因为之前的会话可能已失效
                # English: Get the link object again as the previous session might be invalid
                link_for_status = await crud.link.get(db=db, id=link_id)
                if link_for_status:
                    error_msg = f"Processing Exception: {e}"
                    # 中文: 异常导致失败, is_success 默认为 False
                    # English: Exception caused failure, is_success defaults to False
                    await crud.link.update_status(db=db, db_obj=link_for_status, status=LinkStatus.ERROR, error_message=error_msg)
                    await crud.history_log.create_log(
                        db=db,
                        link_id=link_id,
                        status=HistoryStatus.FAILURE,
                        error_message=error_msg
                    )
            except Exception as inner_e:
                logger.error(f"Failed to update link {link_id} status and log history after exception: {inner_e}")
        finally:
            logger.info(f"Finished processing for link_id: {link_id}")


async def trigger_monitoring_job():
    """
    中文: 由调度器调用的作业函数, 用于触发所有启用链接的监控。
    English: Job function called by the scheduler to trigger monitoring for all enabled links.

    它会异步地为每个链接启动 process_link 任务。
    It asynchronously starts the process_link task for each link.
    """
    logger.info("Scheduler triggered: Starting monitoring job for all enabled links...")
    tasks = []
    # 中文: 使用 Semaphore 限制并发任务数量 / Use Semaphore to limit the number of concurrent tasks
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)

    async with AsyncSessionFactory() as db:
        # 中文: 获取所有需要处理的链接 (启用状态, 并且当前不是正在处理的状态)
        # English: Get all links that need processing (enabled and not currently being processed)
        query = select(Link).where(
            Link.is_enabled == True,
            Link.status.notin_([LinkStatus.DOWNLOADING, LinkStatus.RECORDING, LinkStatus.MONITORING])
        )
        enabled_links = (await db.execute(query)).scalars().all()
        if not enabled_links:
            logger.info("Scheduler job: No enabled and idle links found to process.")
            return

        count = 0
        async def process_link_with_semaphore(link_id: int, sem: asyncio.Semaphore):
            async with sem:
                await process_link(link_id)

        for link in enabled_links:
            # 中文: 创建 asyncio 任务来并发处理链接, 并通过 semaphore 控制并发数
            # English: Create asyncio tasks to process links concurrently, controlled by the semaphore
            tasks.append(asyncio.create_task(process_link_with_semaphore(link.id, semaphore)))
            count += 1
            logger.info(f"Scheduler job: Created task for link_id: {link.id} ({link.url})")

    if tasks:
        # 中文: 等待所有创建的 process_link 任务完成
        # English: Wait for all created process_link tasks to complete
        await asyncio.gather(*tasks)
        logger.info(f"Scheduler job: Finished processing {count} links.")
    else:
        logger.info("Scheduler job: No tasks were created.")
