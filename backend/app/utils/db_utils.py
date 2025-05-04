# -*- coding: utf-8 -*-
# /usr/bin/env python3

import asyncio
import logging
import os
import shutil
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

async def export_database_to_sql(output_filename: str) -> bool:
    """
    中文: 将 SQLite 数据库导出为 SQL 文件。
    English: Export the SQLite database to an SQL file.

    使用 sqlite3 命令行工具执行 .dump 命令。
    Uses the sqlite3 command-line tool to execute the .dump command.

    参数 / Parameters:
        output_filename: 导出的 SQL 文件名 (完整路径) / The output SQL filename (full path).

    返回 / Returns:
        bool: 操作是否成功 / Whether the operation was successful.
    """
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at: {db_path}")
        return False

    # 中文: 检查 sqlite3 命令是否存在
    # English: Check if the sqlite3 command exists
    sqlite3_cmd = shutil.which("sqlite3")
    if not sqlite3_cmd:
        logger.error("sqlite3 command not found. Please install SQLite command-line tools.")
        # 或者可以尝试使用 Python 内置的 sqlite3 模块的 iterdump() 方法作为备选
        # Alternatively, try using the iterdump() method of Python's built-in sqlite3 module as a fallback
        return False

    command = f'"{sqlite3_cmd}" "{db_path}" .dump'
    logger.info(f"Executing database export command: {command}")

    try:
        # 中文: 使用 asyncio.create_subprocess_shell 执行命令并将输出重定向到文件
        # English: Use asyncio.create_subprocess_shell to execute the command and redirect output to a file
        with open(output_filename, "w", encoding="utf-8") as outfile:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=outfile, # 将标准输出写入文件 / Write stdout to file
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"Database successfully exported to: {output_filename}")
            return True
        else:
            error_message = stderr.decode().strip() if stderr else "Unknown error"
            logger.error(f"Database export failed. Return code: {process.returncode}. Error: {error_message}")
            # 中文: 如果失败, 删除可能已创建的不完整文件
            # English: If failed, delete the potentially created incomplete file
            if os.path.exists(output_filename):
                os.remove(output_filename)
            return False
    except Exception as e:
        logger.error(f"Exception during database export: {e}", exc_info=True)
        if os.path.exists(output_filename):
            os.remove(output_filename)
        return False

async def import_database_from_sql(sql_filepath: str) -> bool:
    """
    中文: 从 SQL 文件导入数据到 SQLite 数据库。
    English: Import data from an SQL file into the SQLite database.

    警告: 此操作会先删除当前的数据库文件, 然后执行 SQL 文件!
    Warning: This operation will first delete the current database file and then execute the SQL file!

    参数 / Parameters:
        sql_filepath: 要导入的 SQL 文件路径 / Path to the SQL file to import.

    返回 / Returns:
        bool: 操作是否成功 / Whether the operation was successful.
    """
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    sqlite3_cmd = shutil.which("sqlite3")

    if not os.path.exists(sql_filepath):
        logger.error(f"SQL file not found for import: {sql_filepath}")
        return False
    if not sqlite3_cmd:
        logger.error("sqlite3 command not found. Cannot perform import.")
        return False

    # 中文: 关键步骤: 删除现有数据库文件!
    # English: Critical step: Delete the existing database file!
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logger.warning(f"Existing database file deleted: {db_path}")
        except Exception as e:
            logger.error(f"Failed to delete existing database file {db_path}: {e}", exc_info=True)
            return False

    # 中文: 执行导入命令
    # English: Execute the import command
    command = f'"{sqlite3_cmd}" "{db_path}" < "{sql_filepath}"'
    logger.info(f"Executing database import command...") # 不记录完整命令以防文件路径敏感 / Don't log full command in case file path is sensitive

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"Database successfully imported from: {sql_filepath}")
            # 中文: 导入成功后, 可能需要重新初始化数据库连接或重启应用以使更改生效
            # English: After successful import, may need to re-initialize DB connection or restart app for changes to take effect
            # 这里我们假设调用者会处理后续事宜 / Here we assume the caller handles subsequent actions
            return True
        else:
            error_message = stderr.decode().strip() if stderr else "Unknown error"
            logger.error(f"Database import failed. Return code: {process.returncode}. Error: {error_message}")
            # 中文: 导入失败后, 数据库文件可能处于不一致状态 / After import failure, DB file might be in inconsistent state
            return False
    except Exception as e:
        logger.error(f"Exception during database import: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # 中文: 测试导出和导入功能
    # English: Test export and import functions
    async def test_db_utils():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = os.path.join(settings.MEDIA_ROOT, f"db_export_test_{timestamp}.sql")
        print(f"Attempting to export database to: {export_file}")
        success = await export_database_to_sql(export_file)
        if success:
            print("Export successful.")
            # print(f"\nAttempting to import database from: {export_file}")
            # import_success = await import_database_from_sql(export_file)
            # if import_success:
            #     print("Import successful (database was overwritten).")
            # else:
            #     print("Import failed.")
            # os.remove(export_file) # 清理测试文件 / Clean up test file
        else:
            print("Export failed.")

    # asyncio.run(test_db_utils()) # 取消注释以运行测试 / Uncomment to run test
    print("DB Utils module loaded. Run with test_db_utils() for basic checks.")
