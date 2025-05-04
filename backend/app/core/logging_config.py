# -*- coding: utf-8 -*-
# /usr/bin/env python3

import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# 从 app.core.config 导入 settings 实例和 PROJECT_ROOT 常量
# Import settings instance and PROJECT_ROOT constant from app.core.config
from app.core.config import settings, PROJECT_ROOT

def setup_logging():
    """
    中文: 配置应用程序的日志记录。
    English: Configures logging for the application.

    设置控制台和文件日志处理器。
    Sets up console and file log handlers.
    """
    # 中文: 获取根日志记录器
    # English: Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # 中文: 设置默认日志级别为 INFO / English: Set default log level to INFO

    # 中文: 创建日志格式器
    # English: Create a log formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 中文: 创建控制台处理器
    # English: Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # 中文: 控制台输出 INFO 及以上级别的日志 / English: Console outputs INFO level and above logs
    console_handler.setFormatter(formatter)

    # 中文: 创建文件处理器 (可选)
    # English: Create a file handler (optional)
    # 可以根据需要配置日志文件路径、大小和备份数量
    # Can configure log file path, size, and backup count as needed
    # 直接使用导入的 PROJECT_ROOT 常量 / Use the imported PROJECT_ROOT constant directly
    log_dir = os.path.join(PROJECT_ROOT, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "app.log")

    # 中文: 使用 RotatingFileHandler 实现日志文件轮转
    # English: Use RotatingFileHandler for log file rotation
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=1024 * 1024 * 5, # 5 MB
        backupCount=5, # 保留 5 个备份文件 / Keep 5 backup files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO) # 中文: 文件记录 INFO 及以上级别的日志 / English: File logs INFO level and above
    file_handler.setFormatter(formatter)

    # 中文: 清除现有的处理器, 避免重复添加
    # English: Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 中文: 添加处理器到根日志记录器
    # English: Add handlers to the root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 中文: 配置 uvicorn 日志记录器, 避免重复输出
    # English: Configure uvicorn loggers to avoid duplicate output
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = False

    logger = logging.getLogger(__name__)
    logger.info("Logging configured.")

if __name__ == "__main__":
    # 中文: 测试日志配置
    # English: Test logging configuration
    setup_logging()
    test_logger = logging.getLogger(__name__)
    test_logger.debug("This is a debug message.")
    test_logger.info("This is an info message.")
    test_logger.warning("This is a warning message.")
    test_logger.error("This is an error message.")
    test_logger.critical("This is a critical message.")
