# -*- coding: utf-8 -*-
# /usr/bin/env python3

import os
import logging
import tempfile
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends # 导入 Depends / Import Depends
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask # 导入 BackgroundTask / Import BackgroundTask

from app.utils import export_database_to_sql, import_database_from_sql
from app.core.config import settings
from app.api import deps # 导入认证依赖 / Import authentication dependencies
from app import models # 导入 models / Import models

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/export", response_class=FileResponse, dependencies=[Depends(deps.get_current_active_user)])
async def export_db(
    # current_user: models.User = Depends(deps.get_current_active_user) # 获取当前用户 (如果需要记录操作者) / Get current user (if operator logging is needed)
):
    """
    中文: 导出整个数据库为 SQL 文件并提供下载。
    English: Export the entire database as an SQL file and provide it for download.
    """
    # 中文: 创建一个临时文件来存储导出的 SQL
    # English: Create a temporary file to store the exported SQL
    # 使用 NamedTemporaryFile 并在 FileResponse 中处理删除可能更优雅
    # Using NamedTemporaryFile and handling deletion in FileResponse might be more elegant
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.gettempdir()
    export_filename = os.path.join(temp_dir, f"media_auto_saver_backup_{timestamp}.sql")

    logger.info(f"Attempting database export to temporary file: {export_filename}")
    success = await export_database_to_sql(export_filename)

    if not success:
        raise HTTPException(status_code=500, detail="Database export failed.")

    # 中文: 使用 FileResponse 发送文件, FastAPI 会在发送后自动清理临时文件 (如果使用 BackgroundTasks)
    # English: Use FileResponse to send the file, FastAPI handles cleanup if using BackgroundTasks for deletion
    # 中文: 使用 FileResponse 发送文件, 并添加后台任务删除临时文件
    # English: Use FileResponse to send the file, and add a background task to delete the temporary file
    return FileResponse(
        path=export_filename,
        filename=f"media_auto_saver_backup_{timestamp}.sql",
        media_type='application/sql',
        background=BackgroundTask(os.remove, export_filename) # 添加后台任务删除文件 / Add background task to delete file
    )

@router.post("/import", dependencies=[Depends(deps.get_current_active_user)])
async def import_db(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="上传 SQL 文件进行导入 / Upload SQL file for import"),
    # current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    中文: 上传 SQL 文件并导入数据库。警告: 这将覆盖当前数据库!
    English: Upload an SQL file and import the database. Warning: This will overwrite the current database!
    """
    # 中文: 检查上传的文件类型
    # English: Check the uploaded file type
    if not file.filename.endswith(".sql"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .sql file.")

    # 中文: 将上传的文件保存到临时位置
    # English: Save the uploaded file to a temporary location
    try:
        # 使用 mkstemp 获取一个安全的文件名和文件描述符
        # Use mkstemp to get a secure filename and file descriptor
        fd, temp_filepath = tempfile.mkstemp(suffix=".sql")
        with os.fdopen(fd, "wb") as temp_file:
            # 分块读取上传的文件内容并写入临时文件
            # Read uploaded file content in chunks and write to temp file
            while content := await file.read(1024 * 1024): # Read 1MB chunks
                temp_file.write(content)
        logger.info(f"Uploaded SQL file saved temporarily to: {temp_filepath}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
    finally:
        await file.close() # 确保文件关闭 / Ensure file is closed

    # 中文: 在后台任务中执行导入操作, 并在完成后删除临时文件
    # English: Perform the import operation in a background task and delete the temp file afterwards
    background_tasks.add_task(run_import_and_cleanup, temp_filepath)

    return {"message": "Database import process started in the background. "
                     "The application might restart or become temporarily unavailable. "
                     "Please check server logs for status."}

async def run_import_and_cleanup(temp_filepath: str):
    """
    中文: 执行数据库导入并清理临时文件的后台任务。
    English: Background task to perform database import and clean up the temporary file.
    """
    logger.info(f"Background task started: Importing database from {temp_filepath}")
    success = await import_database_from_sql(temp_filepath)
    if success:
        logger.info("Background task: Database import successful.")
        # 中文: 导入成功后, 可能需要通知管理员或触发应用重载 (如果 uvicorn --reload 不够)
        # English: After success, might need to notify admin or trigger app reload (if uvicorn --reload isn't sufficient)
    else:
        logger.error("Background task: Database import failed.")

    # 中文: 清理临时 SQL 文件
    # English: Clean up the temporary SQL file
    try:
        os.remove(temp_filepath)
        logger.info(f"Background task: Temporary import file deleted: {temp_filepath}")
    except Exception as e:
        logger.error(f"Background task: Failed to delete temporary import file {temp_filepath}: {e}")

    # 中文: 考虑在导入后如何平滑地让应用使用新数据库
    # English: Consider how to smoothly let the app use the new database after import
    # 可能需要重启 uvicorn 进程 / May need to restart the uvicorn process
    logger.warning("Database import finished. Application restart might be required for changes to fully apply.")
