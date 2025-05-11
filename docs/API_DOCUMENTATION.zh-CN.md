# Media Auto Saver API 文档

本文档提供了 Media Auto Saver 后端 API 的详细信息。所有 API 端点的基础路径为 `/api/v1`。

**注意**: 更详细和交互式的 API 文档可以通过在本地运行后端服务后访问 `http://localhost:8000/api/v1/docs` (Swagger UI) 或 `http://localhost:8000/api/v1/redoc` (ReDoc) 来获取。

## 目录

- [认证](#认证)
- [用户管理 (Users)](#用户管理-users)
- [登录 (Login)](#登录-login)
- [密码重置 (Password Reset)](#密码重置-password-reset)
- [链接管理 (Links)](#链接管理-links)
- [下载历史 (History)](#下载历史-history)
- [设置 (Settings)](#设置-settings)
- [数据库管理 (Database)](#数据库管理-database) - (根据 `database.py` 的实际功能填写)
- [通用响应格式](#通用响应格式)
- [错误处理](#错误处理)

## 认证

大多数 API 端点需要通过 JWT (JSON Web Token)进行认证。在成功登录后，客户端会收到一个 `access_token`。客户端应在后续请求的 `Authorization` HTTP 头部中包含此令牌，格式为 `Bearer <access_token>`。

## 用户管理 (Users)

基础路径: `/users`

### `POST /users/`
- **描述**: 创建一个新用户 (通常由管理员操作，或在初始设置时开放注册)。
- **请求体**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "username": "newuser"
    // "is_active": true, (可选, 通常默认为 true)
    // "is_superuser": false (可选, 通常默认为 false)
  }
  ```
- **成功响应 (200 OK)**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "username": "newuser",
    "is_active": true,
    "is_superuser": false
  }
  ```
- **需要认证**: 是 (通常需要超级用户权限)

### `GET /users/me`
- **描述**: 获取当前已认证用户的信息。
- **成功响应 (200 OK)**: (同上，返回当前用户信息)
- **需要认证**: 是

### `PUT /users/me`
- **描述**: 更新当前已认证用户的信息 (例如，修改邮箱、密码)。
- **请求体**:
  ```json
  {
    "email": "new_email@example.com", // 可选
    "password": "new_secure_password", // 可选
    "username": "current_username" // 可选
  }
  ```
- **成功响应 (200 OK)**: (返回更新后的用户信息)
- **需要认证**: 是

### `GET /users/{user_id}`
- **描述**: 获取指定 ID 用户的信息 (通常由管理员操作)。
- **路径参数**: `user_id` (integer)
- **成功响应 (200 OK)**: (返回指定用户信息)
- **需要认证**: 是 (通常需要超级用户权限)

### `PUT /users/{user_id}`
- **描述**: 更新指定 ID 用户的信息 (通常由管理员操作)。
- **路径参数**: `user_id` (integer)
- **请求体**: (同 `POST /users/`，但用于更新)
- **成功响应 (200 OK)**: (返回更新后的用户信息)
- **需要认证**: 是 (通常需要超级用户权限)

## 登录 (Login)

基础路径: `/login`

### `POST /login/access-token`
- **描述**: 用户登录并获取 JWT 访问令牌。
- **请求体 (form data)**:
  - `username`: 用户的用户名或邮箱
  - `password`: 用户的密码
- **成功响应 (200 OK)**:
  ```json
  {
    "access_token": "your_jwt_token_here",
    "token_type": "bearer"
  }
  ```
- **需要认证**: 否

### `POST /login/test-token`
- **描述**: 测试提供的访问令牌是否有效。
- **成功响应 (200 OK)**: (返回当前令牌对应的用户信息)
- **需要认证**: 是

## 密码重置 (Password Reset)

基础路径: `/password-reset`

### `POST /password-reset/request-reset`
- **描述**: 请求密码重置。后端通常会生成一个重置令牌并通过邮件发送给用户（如果邮件服务已配置）。
- **请求体**:
  ```json
  {
    "email": "user_to_reset@example.com"
  }
  ```
- **成功响应 (200 OK)**:
  ```json
  {
    "msg": "Password reset email sent" // 或类似消息
  }
  ```
- **需要认证**: 否

### `POST /password-reset/reset`
- **描述**: 使用有效的重置令牌设置新密码。
- **请求体**:
  ```json
  {
    "token": "valid_reset_token_here",
    "new_password": "new_strong_password"
  }
  ```
- **成功响应 (200 OK)**:
  ```json
  {
    "msg": "Password updated successfully"
  }
  ```
- **需要认证**: 否

## 链接管理 (Links)

基础路径: `/links`

### `POST /links/`
- **描述**: 添加一个新的媒体链接。
- **请求体**:
  ```json
  {
    "url": "https://www.youtube.com/channel/...",
    "name": "My Favorite Channel",
    "type": "youtube_channel", // e.g., youtube_channel, pixiv_user, generic_video, generic_gallery
    "is_enabled": true,
    "download_automatically": true,
    "tags": ["tag1", "tag2"], // 可选
    "cookies": "{ \"cookie_name\": \"cookie_value\" }" // 可选, JSON string for specific cookies
  }
  ```
- **成功响应 (200 OK)**: (返回创建的链接对象，包含 `id`)
- **需要认证**: 是

### `GET /links/`
- **描述**: 获取所有链接列表，支持分页。
- **查询参数**:
  - `skip` (integer, optional, default: 0): 跳过的记录数。
  - `limit` (integer, optional, default: 100): 返回的最大记录数。
- **成功响应 (200 OK)**: (返回链接对象列表)
- **需要认证**: 是

### `GET /links/{link_id}`
- **描述**: 获取指定 ID 的链接信息。
- **路径参数**: `link_id` (integer)
- **成功响应 (200 OK)**: (返回指定的链接对象)
- **需要认证**: 是

### `PUT /links/{link_id}`
- **描述**: 更新指定 ID 的链接信息。
- **路径参数**: `link_id` (integer)
- **请求体**: (同 `POST /links/`，但用于更新)
- **成功响应 (200 OK)**: (返回更新后的链接对象)
- **需要认证**: 是

### `DELETE /links/{link_id}`
- **描述**: 删除指定 ID 的链接。
- **路径参数**: `link_id` (integer)
- **成功响应 (200 OK)**: (返回被删除的链接对象或确认消息)
- **需要认证**: 是

### `POST /links/{link_id}/trigger-download`
- **描述**: 手动触发指定链接的下载检查。
- **路径参数**: `link_id` (integer)
- **成功响应 (200 OK)**:
  ```json
  {
    "msg": "Download triggered for link X"
  }
  ```
- **需要认证**: 是

## 下载历史 (History)

基础路径: `/history`

### `GET /history/`
- **描述**: 获取下载历史记录，支持分页和过滤。
- **查询参数**:
  - `skip` (integer, optional, default: 0)
  - `limit` (integer, optional, default: 100)
  - `link_id` (integer, optional): 按链接 ID 过滤。
  - `status` (string, optional): 按下载状态过滤 (e.g., "success", "failure")。
- **成功响应 (200 OK)**: (返回历史记录对象列表)
  ```json
  // 示例单个历史记录对象
  {
    "id": 1,
    "link_id": 1,
    "link_name": "My Favorite Channel",
    "timestamp": "2023-10-27T10:30:00Z",
    "status": "success",
    "message": "Downloaded 3 new items.",
    "downloaded_files": ["file1.mp4", "file2.jpg"] // 实际下载的文件列表
  }
  ```
- **需要认证**: 是

### `GET /history/{history_id}`
- **描述**: 获取指定 ID 的下载历史记录。
- **路径参数**: `history_id` (integer)
- **成功响应 (200 OK)**: (返回指定的历史记录对象)
- **需要认证**: 是

## 设置 (Settings)

基础路径: `/settings`

### `GET /settings/`
- **描述**: 获取当前应用设置。
- **成功响应 (200 OK)**:
  ```json
  {
    "link_monitor_interval_minutes": 60,
    "max_concurrent_downloads": 5,
    "media_root": "/path/to/media",
    "site_cookies_json": "{\"pixiv\": \"/path/to/pixiv_cookies.txt\"}" // 示例
    // 其他可配置项
  }
  ```
- **需要认证**: 是 (通常需要超级用户权限)

### `PUT /settings/`
- **描述**: 更新应用设置。
- **请求体**: (同 `GET /settings/` 的响应结构，但用于更新)
- **成功响应 (200 OK)**: (返回更新后的设置对象)
- **需要认证**: 是 (通常需要超级用户权限)

## 数据库管理 (Database)

基础路径: `/database`

这些端点用于数据库的导入和导出，操作需谨慎，特别是导入操作会覆盖现有数据。

### `GET /database/export`
- **描述**: 导出整个数据库为 SQL 文件并提供下载。
- **响应类型**: `application/sql` (文件下载)
- **成功响应**: 直接下载名为 `media_auto_saver_backup_YYYYMMDD_HHMMSS.sql` 的 SQL 文件。
- **需要认证**: 是 (需要已激活用户权限)

### `POST /database/import`
- **描述**: 上传 SQL 文件并导入数据库。**警告: 此操作将覆盖当前数据库!** 导入过程在后台执行。
- **请求体 (form data)**:
  - `file`: 必需，要上传的 `.sql` 文件。
- **成功响应 (200 OK)**:
  ```json
  {
    "message": "Database import process started in the background. The application might restart or become temporarily unavailable. Please check server logs for status."
  }
  ```
- **需要认证**: 是 (需要已激活用户权限)
- **注意**:
  - 只接受 `.sql` 文件。
  - 导入操作可能导致应用暂时不可用或需要重启。

## 通用响应格式

- 成功请求通常返回 `200 OK` 或 `201 Created` (对于 `POST` 创建资源)。
- 响应体通常是 JSON 格式。

## 错误处理

- **400 Bad Request**: 请求无效 (例如，缺少必需参数，参数格式错误)。响应体通常包含详细错误信息。
  ```json
  {
    "detail": "Validation Error",
    "errors": [
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
  ```
- **401 Unauthorized**: 未提供有效的认证令牌，或令牌无效/过期。
  ```json
  {
    "detail": "Not authenticated"
  }
  ```
- **403 Forbidden**: 用户已认证，但没有权限执行该操作。
  ```json
  {
    "detail": "The user doesn't have enough privileges"
  }
  ```
- **404 Not Found**: 请求的资源不存在。
  ```json
  {
    "detail": "Item not found"
  }
  ```
- **422 Unprocessable Entity**: 请求体格式正确，但包含语义错误 (FastAPI 常用于 Pydantic 验证失败)。
  ```json
  {
    "detail": [
      {
        "loc": ["body", "field_name"],
        "msg": "Specific validation error message",
        "type": "validation_error_type"
      }
    ]
  }
  ```
- **500 Internal Server Error**: 服务器端发生未知错误。
