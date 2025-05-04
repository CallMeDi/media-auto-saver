# -*- coding: utf-8 -*-
# /usr/bin/env python3

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from sqlmodel import select
from app.api.v1.api import api_router as api_v1_router # 导入 v1 路由 / Import v1 router
from app.core.config import settings # 导入配置 / Import settings
from app.core.logging_config import setup_logging # 导入日志配置函数 / Import logging configuration function
from app.db.session import init_db, AsyncSessionFactory # 导入数据库初始化函数和会话工厂 / Import DB init function and session factory
from app.tasks.scheduler import scheduler, start_scheduler, shutdown_scheduler # 导入调度器 / Import scheduler
from app.tasks.link_monitor import trigger_monitoring_job # 导入监控任务 / Import monitoring job
from app.models.link import Link, LinkStatus # 导入链接模型和状态 / Import Link model and status
from app import crud, models # 导入 CRUD 操作和 models / Import CRUD operations and models

# 中文: 获取日志记录器 (已在 lifespan 中配置)
# English: Get logger (configured in lifespan)
logger = logging.getLogger(__name__)

# 中文: 定义一个异步上下文管理器来处理应用的启动和关闭事件
# English: Define an asynchronous context manager to handle application startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 中文: 在应用启动时执行的代码
    # English: Code to run when the application starts up
    setup_logging() # 中文: 设置日志配置 / English: Set up logging configuration
    logger.info("Application startup...")
    logger.info("Initializing database...")
    # 中文: 初始化数据库 (创建表)
    # English: Initialize the database (create tables)
    await init_db()
    logger.info("Database initialized.")

    # 中文: 创建初始超级用户 (如果不存在)
    # English: Create initial superuser (if none exists)
    logger.info("Checking for initial superuser...")
    async with AsyncSessionFactory() as db:
        # 检查是否已存在任何用户 (或特定超级用户)
        # Check if any user (or specific superuser) already exists
        query = select(models.User).where(models.User.is_superuser == True).limit(1)
        superuser = (await db.execute(query)).scalars().first()
        if not superuser:
            # 使用 settings 中的值, 如果未设置则使用默认值
            # Use values from settings, falling back to defaults if not set
            initial_username = settings.INITIAL_SUPERUSER_USERNAME or "admin"
            initial_password = settings.INITIAL_SUPERUSER_PASSWORD or "changeme" # 强烈建议修改! / Strongly recommend changing this!
            #initial_email = settings.INITIAL_SUPERUSER_EMAIL or "admin@example.com"

            # 检查是否使用了默认密码 (如果密码是从 settings 加载的, 即使是 'changeme', 也认为已设置)
            # Check if the default password is being used (if loaded from settings, even 'changeme' is considered set)
            using_default_password = settings.INITIAL_SUPERUSER_PASSWORD is None

            if settings.INITIAL_SUPERUSER_USERNAME is None or using_default_password:
                 logger.warning(f"INITIAL_SUPERUSER_USERNAME or INITIAL_SUPERUSER_PASSWORD not set in environment/config. Using defaults.")
                 logger.warning(f"Default superuser username: '{initial_username}', password: '{'changeme' if using_default_password else '********'}'")
            else:
                 logger.info(f"Using initial superuser credentials from environment/config.")
                 logger.info(f"Initial superuser username: '{initial_username}'")

            logger.info(f"Creating initial superuser '{initial_username}'...")
            user_in = models.UserCreate(
                username=initial_username,
                password=initial_password, # 使用从 settings 或默认值获取的密码 / Use password from settings or default
                #email=initial_email,
                is_superuser=True,
                is_active=True # 确保初始用户是激活的 / Ensure initial user is active
            )
            try:
                await crud.user.create(db=db, obj_in=user_in)
                logger.info(f"Initial superuser '{initial_username}' created successfully.")
            except Exception as e:
                logger.error(f"Failed to create initial superuser '{initial_username}': {e}", exc_info=True)
        else:
            logger.info("Superuser already exists.")


    # 中文: 重置启动时处于中间状态的链接
    # English: Reset links that were in an intermediate state on startup
    logger.info("Resetting links in intermediate states...")
    async with AsyncSessionFactory() as db:
        intermediate_statuses = [LinkStatus.DOWNLOADING, LinkStatus.RECORDING, LinkStatus.MONITORING]
        query = select(Link).where(Link.status.in_(intermediate_statuses))
        links_to_reset = (await db.execute(query)).scalars().all()
        reset_count = 0
        for link in links_to_reset:
            # 可以选择重置为 IDLE 或 ERROR, 这里选择 IDLE
            # Can choose to reset to IDLE or ERROR, here we choose IDLE
            await crud.link.update_status(db=db, db_obj=link, status=LinkStatus.IDLE, error_message="Reset on startup")
            reset_count += 1
        if reset_count > 0:
            logger.info(f"Reset {reset_count} links to IDLE status.")
        else:
            logger.info("No links found in intermediate states.")

    # 中文: 添加周期性监控任务 (例如: 每小时运行一次)
    # English: Add periodic monitoring job (e.g., run every hour)
    # 使用 settings 中配置的间隔 / Use interval configured in settings
    logger.info(f"Scheduling link monitoring job with interval: {settings.LINK_MONITOR_INTERVAL_MINUTES} minutes.")
    scheduler.add_job(
        trigger_monitoring_job,
        'interval',
        minutes=settings.LINK_MONITOR_INTERVAL_MINUTES, # 从配置读取间隔 / Read interval from config
        id='monitor_all_links_job',
        replace_existing=True
    )
    logger.info("Scheduled monitoring job.")

    # 中文: 启动调度器
    # English: Start the scheduler
    start_scheduler()

    yield # 应用在此处运行 / Application runs here

    # 中文: 在应用关闭时执行的代码
    # English: Code to run when the application shuts down
    logger.info("Application shutdown...")
    # 中文: 关闭调度器
    # English: Shutdown the scheduler
    shutdown_scheduler()
    logger.info("Scheduler shut down complete.")

# 中文: 创建 FastAPI 应用实例, 并指定 lifespan 管理器
# English: Create FastAPI application instance and specify the lifespan manager
app = FastAPI(
    title="Media Auto Saver API", # API 标题 / API Title
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # OpenAPI schema 路径 / OpenAPI schema path
    lifespan=lifespan
)

# 中文: 包含 v1 API 路由
# English: Include the v1 API router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# 中文: 定义一个简单的根路由用于测试 (可选, 可以移除)
# English: Define a simple root route for testing (optional, can be removed)
@app.get("/")
async def read_root():
    # 中文: 返回一个简单的 JSON 响应
    # English: Return a simple JSON response
    return {"message": "欢迎使用 Media Auto Saver API / Welcome to Media Auto Saver API"}

# 中文: 在脚本直接运行时, 启动 uvicorn 服务器 (主要用于开发)
# English: When the script is run directly, start the uvicorn server (mainly for development)
if __name__ == "__main__":
    import uvicorn
    # 中文: 运行 uvicorn 服务器, 监听 0.0.0.0:8000, 开启热重载
    # English: Run the uvicorn server, listen on 0.0.0.0:8000, enable hot reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
