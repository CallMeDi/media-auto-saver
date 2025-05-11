# Media Auto Saver 架构文档

本文档概述了 Media Auto Saver 项目的技术架构，包括后端、前端以及它们之间的交互。

## 目录

- [Media Auto Saver 架构文档](#media-auto-saver-架构文档)
  - [目录](#目录)
  - [概述](#概述)
  - [技术栈](#技术栈)
  - [后端架构](#后端架构)
    - [后端主要组件](#后端主要组件)
    - [后端目录结构 (backend/app)](#后端目录结构-backendapp)
    - [数据库](#数据库)
    - [后台任务与调度](#后台任务与调度)
    - [外部工具集成](#外部工具集成)
  - [前端架构](#前端架构)
    - [前端主要组件](#前端主要组件)
    - [前端目录结构 (frontend/src)](#前端目录结构-frontendsrc)
    - [状态管理](#状态管理)
    - [路由](#路由)
  - [前后端交互](#前后端交互)
    - [API](#api)
    - [认证机制](#认证机制)
  - [数据流示例](#数据流示例)
    - [用户添加新链接](#用户添加新链接)
    - [自动监控和下载](#自动监控和下载)
  - [未来可能的改进方向](#未来可能的改进方向)

## 概述

Media Auto Saver 是一个全栈 Web 应用程序，旨在自动从各种网站下载媒体内容。它由一个 Python FastAPI 后端和一个 Vue.js 前端组成。

- **后端**: 负责处理业务逻辑、API 请求、数据库交互、用户认证、以及通过调度任务来监控和下载媒体。
- **前端**: 提供用户界面，允许用户管理链接、查看下载历史、配置设置以及与后端 API 进行交互。

## 技术栈

- **后端**:
  - 语言: Python 3.8+
  - Web 框架: FastAPI
  - 数据库: SQLite (通过 SQLModel ORM)
  - 异步任务调度: APScheduler
  - 媒体下载: `yt-dlp`, `gallery-dl` (作为外部 CLI 工具调用)
  - 认证: JWT (JSON Web Tokens)
  - 服务器: Uvicorn
- **前端**:
  - 框架: Vue.js 3
  - 构建工具: Vite
  - 状态管理: Pinia
  - HTTP 客户端: Axios
  - 路由: Vue Router
  - UI 组件库: (目前看来是自定义组件，未来可以考虑引入如 Vuetify, Element Plus 等)

## 后端架构

后端采用 FastAPI 构建，这是一个现代、快速（高性能）的 Python Web 框架，用于构建 API。

### 后端主要组件

1.  **API Endpoints**: 定义了客户端可以访问的 HTTP 接口，用于处理用户请求、链接管理、历史记录查看等。
2.  **业务逻辑层 (Services/CRUD)**: 包含核心的业务逻辑，例如如何处理链接、如何触发下载、如何管理用户等。
3.  **数据访问层 (Models/CRUD/DB)**: 负责与数据库进行交互，包括数据模型的定义 (SQLModel) 和数据的增删改查操作 (CRUD)。
4.  **核心组件 (Core)**: 包括配置管理、安全相关的函数 (如密码哈希、JWT 生成与验证)、日志配置等。
5.  **后台任务 (Tasks)**: 使用 APScheduler 定期执行的任务，主要是监控启用的链接并触发下载过程。

### 后端目录结构 (backend/app)

-   `api/`: 包含 API 路由定义。
    -   `deps.py`: API 依赖项，例如获取当前用户。
    -   `v1/`: API 版本 1。
        -   `api.py`: 聚合 v1 版本的所有 API 路由器。
        -   `endpoints/`: 包含各个功能的具体 API 路由实现 (如 `links.py`, `users.py`)。
-   `core/`: 核心配置和安全模块。
    -   `config.py`: 应用配置管理 (从环境变量加载)。
    -   `logging_config.py`: 日志配置。
    -   `security.py`:密码哈希、JWT 令牌处理等。
-   `crud/`: 数据增删改查 (CRUD) 操作。
    -   `crud_link.py`, `crud_user.py`, etc.: 针对特定数据模型的 CRUD 函数。
-   `db/`: 数据库连接和会话管理。
    -   `session.py`: 数据库引擎和会话创建。
-   `models/`: SQLModel 数据模型定义 (对应数据库表结构)。
    -   `link.py`, `user.py`, `history.py`, etc.
-   `schemas/`: Pydantic 数据模型，用于 API 请求/响应的数据验证和序列化。
    -   `token.py`: JWT 令牌相关的 schema。
    -   (其他 schema 通常与 `models` 对应，但用于 API 交互)
-   `services/`: 更高层次的业务逻辑，可能会调用 CRUD 操作和外部服务。
    -   `downloader.py`: 封装了 `yt-dlp` 和 `gallery-dl` 的下载逻辑。
-   `tasks/`: 后台任务定义。
    -   `link_monitor.py`: 监控链接并触发下载的任务。
    -   `scheduler.py`: APScheduler 的配置和启动。
-   `tests/`: 单元测试和集成测试。
-   `utils/`: 通用工具函数。
-   `main.py`: FastAPI 应用实例的创建和主要配置。

### 数据库

-   默认使用 SQLite 数据库 (`database.db` 文件存储在项目根目录)。
-   SQLModel 用于 ORM 功能，它结合了 Pydantic 和 SQLAlchemy 的优点，可以方便地定义数据模型并与数据库交互。
-   数据库表包括：用户 (users)、链接 (links)、下载历史 (history)、密码重置令牌 (password_resets) 等。

### 后台任务与调度

-   APScheduler 用于定期执行后台任务。
-   主要任务是 `link_monitor`，它会：
    1.  从数据库获取所有启用的链接。
    2.  检查每个链接是否有新的媒体内容。
    3.  如果发现新内容，则调用 `downloader` 服务进行下载。
    4.  更新下载历史记录。
-   任务的执行频率可以在 `.env` 文件中配置 (`LINK_MONITOR_INTERVAL_MINUTES`)。

### 外部工具集成

-   `yt-dlp`: 用于下载视频和音频内容。
-   `gallery-dl`: 用于下载图片和图集内容。
-   这两个工具通过 `subprocess` 在后端被调用。`downloader.py` 服务封装了调用这些工具的逻辑。

## 前端架构

前端使用 Vue.js 3 构建，采用 Vite 作为开发和构建工具，提供现代化的开发体验。

### 前端主要组件

1.  **Views**: 代表应用中的不同页面 (例如，登录页、链接管理页、历史记录页)。
2.  **Components**: 可重用的 UI 组件 (例如，对话框、表单元素)。
3.  **Layouts**: 定义页面的整体结构和布局。
4.  **Router**: 管理应用的导航和视图切换。
5.  **Store (Pinia)**: 集中管理应用的状态。

### 前端目录结构 (frontend/src)

-   `App.vue`: Vue 应用的根组件。
-   `main.js`: 应用的入口文件，初始化 Vue 实例、路由、Pinia 等。
-   `style.css`: 全局 CSS 样式。
-   `assets/`: 静态资源，如图片、字体等。
-   `components/`: 可重用的 Vue 组件。
    -   `LinkDialog.vue`: 添加/编辑链接的对话框。
-   `layouts/`: 布局组件。
    -   `DefaultLayout.vue`: 应用的主要布局，可能包含导航栏、页脚等。
-   `router/`: Vue Router 配置。
    -   `index.js`: 定义路由规则和导航守卫。
-   `stores/`: Pinia状态管理模块。
    -   `auth.js`: 管理用户认证状态和 Token。
    -   `link.js`: 管理链接相关的数据和操作。
    -   `history.js`: 管理历史记录相关的数据。
    -   `error.js`: 管理全局错误状态。
-   `utils/`: 通用工具函数或常量。
    -   `constants.js`: 应用中使用的常量。
-   `views/`: 页面级 Vue 组件。
    -   `LoginView.vue`, `LinksView.vue`, `HistoryView.vue`, etc.

### 状态管理

-   Pinia 用于全局状态管理。
-   不同的 store模块 (如 `auth.js`, `link.js`) 负责管理应用的不同部分的状态。
-   组件可以通过 Pinia store 获取和修改共享状态，实现组件间的通信和数据同步。

### 路由

-   Vue Router 用于实现单页应用 (SPA) 的客户端路由。
-   `router/index.js` 文件定义了应用的路由表，将 URL 路径映射到对应的视图组件。
-   可能包含路由守卫 (navigation guards) 来处理例如需要登录才能访问的页面的逻辑。

## 前后端交互

### API

-   前端通过 HTTP 请求与后端 FastAPI 提供的 RESTful API 进行通信。
-   API 的基础路径通常是 `/api/v1/`。
-   后端 API 文档 (Swagger UI) 可在后端服务启动后通过 `/api/v1/docs` 访问，提供了所有可用端点的详细信息和测试功能。

### 认证机制

-   用户认证通过 JWT (JSON Web Tokens) 实现。
-   **登录流程**:
    1.  用户在前端输入用户名和密码。
    2.  前端将凭据发送到后端的 `/api/v1/login/access-token` 端点。
    3.  后端验证凭据，如果成功，则生成一个 JWT 并返回给前端。
    4.  前端将 JWT 存储起来 (通常在 localStorage 或 sessionStorage 中)，并在后续的 API 请求中通过 `Authorization` HTTP头部 (Bearer Token) 发送给后端。
-   **受保护的端点**: 后端的大多数 API 端点都需要有效的 JWT 进行认证。FastAPI 的依赖注入系统用于验证令牌并获取当前用户。

## 数据流示例

### 用户添加新链接

1.  **前端**: 用户在 `LinksView.vue` 页面点击 "添加链接" 按钮，打开 `LinkDialog.vue`。
2.  **前端**: 用户填写链接信息 (URL, 名称, 类型等) 并提交。
3.  **前端**: `link.js` store 中的 action被调用，通过 Axios 向后端 `/api/v1/links/` 端点发送 POST 请求，请求体包含链接数据。
4.  **后端**: `links.py` 中的相应 API 端点接收请求。
5.  **后端**: 请求数据通过 Pydantic schema进行验证。
6.  **后端**: `crud_link.py` 中的函数被调用，将新链接数据保存到数据库。
7.  **后端**: 返回成功响应 (通常包含新创建的链接对象) 给前端。
8.  **前端**: `link.js` store 更新状态，`LinksView.vue` 重新渲染以显示新链接。

### 自动监控和下载

1.  **后端 (APScheduler)**: `scheduler.py` 中配置的定时任务触发 `link_monitor.py` 中的监控函数。
2.  **后端**: `link_monitor` 从数据库获取所有启用的链接 (`crud_link.py`)。
3.  **后端**: 对于每个链接，调用相应的逻辑 (可能在 `link_utils.py` 或 `downloader.py` 中) 检查是否有新媒体。
    - 这可能涉及调用 `yt-dlp --dump-json` 或类似命令来获取元数据而不实际下载，或者比较已下载列表和远程列表。
4.  **后端**: 如果检测到新媒体，调用 `downloader.py` 中的下载函数。
5.  **后端 (`downloader.py`)**:
    -   根据链接类型选择 `yt-dlp` 或 `gallery-dl`。
    -   构造相应的 CLI 命令。
    -   使用 `subprocess` 执行下载命令。
    -   媒体文件保存到 `.env` 中配置的 `MEDIA_ROOT` 目录。
6.  **后端**: 下载完成后，更新 `history` 表 (`crud_history.py`) 记录下载状态 (成功/失败) 和相关信息。
7.  **前端 (可选)**: 用户可以在 `HistoryView.vue` 页面查看最新的下载历史，该页面会从后端 `/api/v1/history/` 端点获取数据。

## 未来可能的改进方向

-   **更细致的错误处理和重试机制**: 尤其是在下载过程中。
-   **插件系统**: 允许用户添加对新网站或下载器的支持。
-   **WebSocket**: 用于实时更新前端状态 (例如，下载进度)。
-   **更全面的测试**: 增加单元测试和端到端测试的覆盖率。
-   **容器化**: 使用 Docker 进行部署。
-   **引入 UI 组件库**: 提升前端开发效率和 UI 一致性。

本文档旨在提供一个高层次的架构概览。有关特定模块或功能的更详细信息，请参阅源代码和相关注释。
