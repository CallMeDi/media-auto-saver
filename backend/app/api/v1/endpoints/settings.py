# -*- coding: utf-8 -*-
# /usr/bin/env python3

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Body, status
from pydantic import BaseModel, Field, validator
import json
import os

import json
import os
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Body, status
from pydantic import BaseModel, Field, validator
from dotenv import dotenv_values, set_key # For reading/writing .env

from app import models
from app.api import deps
from app.core.config import settings, PROJECT_ROOT # 导入 settings 和项目根目录 / Import settings and project root

logger = logging.getLogger(__name__)
router = APIRouter()
env_path = os.path.join(PROJECT_ROOT, '.env') # Path to .env file

# --- 模型 / Models ---

class SiteCookiesUpdate(BaseModel):
    site_cookies: Dict[str, str] = Field(..., description="站点 Cookies 映射 / Site cookies mapping")

    @validator('site_cookies')
    def validate_paths_exist(cls, v):
        """验证提供的所有 cookies 文件路径是否存在"""
        for site, path in v.items():
            # 路径可以是相对于项目根目录的, 也可以是绝对路径
            # Path can be relative to project root or absolute
            full_path = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                raise ValueError(f"Cookies file path does not exist or is not a file for site '{site}': {path} (resolved to: {full_path})")
        return v

# --- 端点 / Endpoints ---

@router.get("/cookies", response_model=Dict[str, str])
async def get_global_site_cookies(
    current_user: models.User = Depends(deps.get_current_active_user), # 需要认证 / Requires authentication
) -> Any:
    """
    中文: 获取当前的全局站点 Cookies 配置。
    English: Get the current global site cookies configuration.
    """
    # 注意: 这里直接返回 settings 中的值。更健壮的做法可能是从数据库或专用配置文件读取。
    # Note: Directly returns value from settings. More robust approach might read from DB or dedicated config file.
    return settings.SITE_COOKIES

@router.put("/cookies", status_code=status.HTTP_200_OK)
async def update_global_site_cookies(
    *,
    cookies_in: SiteCookiesUpdate = Body(...),
    current_user: models.User = Depends(deps.get_current_active_superuser), # 限制只有管理员能修改 / Restrict modification to superusers
) -> Any:
    """
    中文: 更新全局站点 Cookies 配置。
    English: Update the global site cookies configuration.

    警告: 这个实现直接修改内存中的 settings 对象, 并且不会持久化!
          重启应用后会丢失更改。需要更复杂的持久化机制 (例如写入 .env 或数据库)。
    Warning: This implementation directly modifies the in-memory settings object and is NOT persistent!
             Changes will be lost on application restart. Needs a more complex persistence mechanism (e.g., writing to .env or DB).
    """
    logger.warning("Updating global site cookies in memory. This change is NOT persistent and will be lost on restart!")
    # 验证路径 (Pydantic 模型已完成) / Validate paths (done by Pydantic model)
    settings.SITE_COOKIES = cookies_in.site_cookies
    # --- Persist changes to .env file ---
    try:
        # Convert the dictionary to a JSON string for storage in .env
        cookies_json_str = json.dumps(cookies_in.site_cookies)

        # Use python-dotenv's set_key to update or add the variable
        # This handles creating the file if it doesn't exist and preserves other variables/comments
        set_key(dotenv_path=env_path, key_to_set="SITE_COOKIES_JSON", value_to_set=cookies_json_str, quote_mode="always")

        # Important: Update the in-memory settings object as well so the change is immediately reflected
        # without needing a restart for the *current* process.
        settings.SITE_COOKIES = cookies_in.site_cookies
        logger.info(f"Global site cookies updated and persisted to {env_path} by user '{current_user.username}'. New config: {settings.SITE_COOKIES}")
        return {"message": "Global site cookies updated and saved successfully."}
    except Exception as e:
        logger.error(f"Failed to persist site cookies to {env_path}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save cookies configuration to .env file: {e}"
        )

# TODO: 添加其他设置相关的 API 端点 / Add other settings-related API endpoints
