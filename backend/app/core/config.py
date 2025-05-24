# -*- coding: utf-8 -*-
# /usr/bin/env python3

import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict # 导入 Dict / Import Dict

# 中文: 获取项目根目录 (media-auto-saver)
# English: Get the project root directory (media-auto-saver)
# __file__ 指向当前文件 (config.py)
# os.path.dirname(__file__) 获取当前文件所在目录 (core)
# os.path.dirname(...) 获取 core 目录的上级目录 (app)
# os.path.dirname(...) 获取 app 目录的上级目录 (backend)
# os.path.dirname(...) 获取 backend 目录的上级目录 (项目根目录)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_COOKIES_BASE_DIR_NAME = "user_cookies" # Define constant for user cookies directory name


class Settings(BaseSettings):
    """
    中文: 应用配置类, 继承自 Pydantic 的 BaseSettings, 可以自动从环境变量或 .env 文件加载配置。
    English: Application settings class, inheriting from Pydantic's BaseSettings,
             which can automatically load settings from environment variables or a .env file.
    """
    # 中文: SQLite 数据库文件的 URL
    # English: URL for the SQLite database file
    # 默认值: 在项目根目录下创建一个名为 database.db 的 SQLite 文件
    # Default value: Create an SQLite file named database.db in the project root directory
    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(PROJECT_ROOT, 'database.db')}"

    # 中文: 媒体文件下载/录制的根目录
    # English: Root directory for downloaded/recorded media files
    # 默认值: 在项目根目录下创建一个名为 media 的目录
    # Default value: Create a directory named media in the project root directory
    MEDIA_ROOT: str = os.path.join(PROJECT_ROOT, "media")

    # 中文: API 地址 (用于生成绝对 URL 等)
    # English: API address (used for generating absolute URLs, etc.)
    API_V1_STR: str = "/api/v1"

    # 中文: JWT 相关的配置 (如果需要认证功能) - 暂时留空
    # English: JWT related settings (if authentication is needed) - leave blank for now
    SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days

    # 中文: 初始超级用户凭证 (建议通过环境变量设置)
    # English: Initial superuser credentials (recommended to set via environment variables)
    INITIAL_SUPERUSER_USERNAME: Optional[str] = None
    INITIAL_SUPERUSER_PASSWORD: Optional[str] = None
    #INITIAL_SUPERUSER_EMAIL: Optional[str] = None # 添加邮箱 / Add email

    # 中文: 全局网站 Cookies 文件路径映射 (站点名称小写 -> 文件路径)
    # English: Global site cookies file path mapping (lowercase site name -> file path)
    # 可以通过环境变量 SITE_COOKIES_JSON='{"weibo": "path/to/weibo.txt", "pixiv": "path/to/pixiv.txt"}' 设置
    # Can be set via environment variable SITE_COOKIES_JSON='{"weibo": "path/to/weibo.txt", "pixiv": "path/to/pixiv.txt"}'
    SITE_COOKIES: Dict[str, str] = {}

    # 中文: 最大并发下载任务数 / Maximum number of concurrent download tasks
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))

    # 中文: 链接监控任务运行间隔 (分钟) / Link monitoring job interval (minutes)
    # 默认值: 60 分钟 / Default: 60 minutes
    LINK_MONITOR_INTERVAL_MINUTES: int = int(os.getenv("LINK_MONITOR_INTERVAL_MINUTES", "60"))

    # 中文: 使用 ConfigDict 替代 class Config / English: Use ConfigDict instead of class Config
    model_config = {
        "env_file": os.path.join(PROJECT_ROOT, '.env'),
        "env_file_encoding": 'utf-8',
        "extra": "ignore" # 忽略 .env 文件中未在模型中定义的额外变量 / Ignore extra variables in .env not defined in the model
    }

# 中文: 创建 Settings 实例, 应用启动时会加载配置
# English: Create an instance of Settings, settings will be loaded when the application starts
settings = Settings()

# 中文: 确保媒体根目录存在
# English: Ensure the media root directory exists
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

# 中文: 确保用户 Cookies 目录存在
# English: Ensure the user cookies directory exists
USER_COOKIES_DIR = os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME)
os.makedirs(USER_COOKIES_DIR, exist_ok=True)


if __name__ == "__main__":
    # 中文: 打印加载的配置信息 (用于测试)
    # English: Print the loaded settings information (for testing)
    print("Project Root:", PROJECT_ROOT)
    print("Loaded Settings:")
    print(settings.model_dump())
    print(f"Database will be stored at: {settings.DATABASE_URL.replace('sqlite+aiosqlite:///', '')}")
    print(f"Media files will be stored under: {settings.MEDIA_ROOT}")
    print(f"User cookies will be stored under: {USER_COOKIES_DIR}")
