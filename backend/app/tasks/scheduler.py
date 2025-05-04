# -*- coding: utf-8 -*-
# /usr/bin/env python3

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from pytz import utc

# 中文: 获取日志记录器 (已在 main.py 中配置)
# English: Get logger (configured in main.py)
logger = logging.getLogger(__name__)

# 中文: 配置 JobStore 和 Executor
# English: Configure JobStore and Executor
jobstores = {
    'default': MemoryJobStore() # 使用内存存储 Job 信息 / Use memory to store Job information
}
executors = {
    'default': AsyncIOExecutor() # 使用 asyncio 执行器 / Use asyncio executor
}
job_defaults = {
    'coalesce': True, # 如果错过了执行时间, 只执行一次 / Execute only once if missed execution time
    'max_instances': 1 # 每个 Job 只允许一个实例同时运行 / Allow only one instance per Job to run concurrently
}

# 中文: 创建并配置 AsyncIOScheduler 实例
# English: Create and configure the AsyncIOScheduler instance
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=utc # 使用 UTC 时区 / Use UTC timezone
)

def start_scheduler():
    """
    中文: 启动调度器。
    English: Start the scheduler.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started.")
    else:
        logger.info("Scheduler is already running.")

def shutdown_scheduler():
    """
    中文: 关闭调度器。
    English: Shutdown the scheduler.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    else:
        logger.info("Scheduler is not running.")

# 中文: 可以在这里添加默认的调度任务 / Default scheduled tasks can be added here
# from .link_monitor import trigger_monitoring_job # 稍后导入 / Import later
# scheduler.add_job(trigger_monitoring_job, 'interval', hours=1, id='monitor_all_links', replace_existing=True)
