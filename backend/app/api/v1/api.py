# -*- coding: utf-8 -*-
# /usr/bin/env python3

from fastapi import APIRouter

from app.api.v1.endpoints import links, history, database, login, password_reset, users, settings # 导入 settings 路由 / Import settings router

# 中文: 创建 v1 版本的 API 路由器
# English: Create the v1 API router
api_router = APIRouter()

# 中文: 包含 links 路由, 并添加前缀和标签
# English: Include the links router, adding a prefix and tags
api_router.include_router(links.router, prefix="/links", tags=["Links"])

# 中文: 包含 history 路由, 并添加前缀和标签
# English: Include the history router, adding a prefix and tags
api_router.include_router(history.router, prefix="/history", tags=["History"])

# 中文: 包含 database 路由, 并添加前缀和标签
# English: Include the database router, adding a prefix and tags
api_router.include_router(database.router, prefix="/database", tags=["Database"])

# 中文: 包含 login 路由, 并添加标签
# English: Include the login router, adding tags
api_router.include_router(login.router, tags=["Login"])

# 中文: 包含 password_reset 路由, 并添加标签
# English: Include the password_reset router, adding tags
api_router.include_router(password_reset.router, tags=["Password Reset"])

# 中文: 包含 users 路由, 并添加前缀和标签
# English: Include the users router, adding a prefix and tags
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 中文: 包含 settings 路由, 并添加前缀和标签
# English: Include the settings router, adding a prefix and tags
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])

# 中文: 在这里可以包含其他 v1 版本的路由
# English: Other v1 routers can be included here
# api_router.include_router(other_endpoint.router, prefix="/other", tags=["other"])
