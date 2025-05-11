# 媒体自动保存器

[English Version](README.md)

“媒体自动保存器”是一个强大的工具，旨在根据用户添加的链接自动从各种网站下载或录制媒体。无论您是想存档您最喜爱的创作者的内容，还是保存直播流，本项目都致力于简化这一过程。

作为一个处于早期阶段的开源项目，我们还有很大的改进空间和许多新功能等待实现。我们热烈欢迎各个层次的贡献者！如果您有新奇的想法或希望帮助改进本项目，请随时参与讨论并贡献您的力量。

## 目录

- [媒体自动保存器](#媒体自动保存器)
  - [目录](#目录)
  - [功能特性](#功能特性)
  - [项目文档与社区](#项目文档与社区)
  - [技术栈](#技术栈)
    - [后端 (Python)](#后端-python)
    - [前端 (Node.js)](#前端-nodejs)
  - [设置与安装](#设置与安装)
  - [运行应用程序](#运行应用程序)

## 功能特性

*   **灵活的链接管理**：添加创作者（例如 YouTube 频道、Pixiv 画师）或特定直播流的链接。
*   **自动化监控**：根据用户可配置的计划，自动监控已启用的链接。
*   **多样化下载**：使用 `yt-dlp` 下载视频/音频，使用 `gallery-dl` 下载图片/画廊。
*   **下载历史记录**：完整记录所有下载尝试（包括成功与失败）。
*   **Web 用户界面**：提供一个用户友好的 Web UI（基于 Vue.js），用于管理链接、查看历史记录和配置设置。
*   **安全认证**：通过 JWT 实现用户认证。
*   **密码管理**：包含密码重置功能。
*   **便捷配置**：可通过简单的 `.env` 文件进行配置。

## 项目文档与社区

想要更深入地了解项目或参与贡献吗？请查阅以下资源：

*   **了解项目：**
    *   架构概览：[中文文档](ARCHITECTURE.md)
    *   API 文档：[中文文档](API_DOCUMENTATION.md)
*   **贡献者指南：**
    *   贡献指南：[中文文档](CONTRIBUTING.md)

我们鼓励计划贡献代码或希望了解技术细节的您阅读这些文档。

## 技术栈

### 后端 (Python)

*   **Python 版本**：3.8+
*   **主要依赖包**：（完整列表请参阅 `backend/requirements.txt`）
    *   FastAPI (Web 框架)
    *   SQLModel (ORM, 配合 aiosqlite 实现异步 SQLite 操作)
    *   Uvicorn (ASGI 服务器)
    *   APScheduler (后台任务调度)
    *   yt-dlp (视频/音频下载)
    *   gallery-dl (图片/画廊下载)
    *   Passlib, python-jose (用户认证及 JWT)
*   **外部命令行工具**：必须安装 `gallery-dl` 并在系统的 PATH 环境变量中可用（通常通过 `requirements.txt` 安装 `gallery-dl` Python 包即可解决）。

### 前端 (Node.js)

*   **Node.js 版本**：请检查 `frontend/package.json` 以确保版本兼容（推荐使用 LTS 版本）。
*   **包管理器**：npm 或 yarn
*   **主要依赖包**：（完整列表请参阅 `frontend/package.json`）
    *   Vue.js 3 (核心前端框架)
    *   Vite (构建工具和开发服务器)
    *   Pinia (状态管理)
    *   Vue Router (路由)
    *   Axios (HTTP 客户端)

## 设置与安装

1.  **克隆仓库：**
    ```bash
    git clone <repository_url> # 请将 <repository_url> 替换为实际的仓库地址
    cd media-auto-saver
    ```

2.  **后端设置：**
    *   （推荐）创建并激活 Python 虚拟环境：
        ```bash
        python3 -m venv venv
        source venv/bin/activate # Linux/macOS
        # venv\Scripts\activate # Windows
        ```
    *   安装后端依赖：
        ```bash
        pip install -r backend/requirements.txt
        ```
    *   验证 `gallery-dl` 命令是否可用：
        ```bash
        gallery-dl --version
        ```

3.  **前端设置：**
    *   进入前端项目目录：
        ```bash
        cd frontend
        ```
    *   安装前端依赖：
        ```bash
        npm install
        # 或 yarn install
        ```
    *   返回项目根目录：
        ```bash
        cd ..
        ```

## 运行应用程序

1.  **运行后端 (FastAPI)：**
    *   确保您当前位于项目根目录 (`media-auto-saver`)。
    *   如果使用了 Python 虚拟环境，请确保它已被激活。
    *   启动 Uvicorn 服务器：
        ```bash
        cd backend
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   API 服务将在 `http://localhost:8000` 上可用。
    *   交互式 API 文档 (Swagger UI) 位于 `http://localhost:8000/api/v1/docs`。

2.  **运行前端 (Vue/Vite)：**
    *   打开一个新的终端窗口。
    *   进入前端项目目录：
        ```bash
        cd frontend
        ```
    *   启动 Vite 开发服务器：
        ```bash
        npm run dev
        # 或 yarn dev
        ```
    *   前端用户界面将在终端中显示的地址可用（通常是 `http://localhost:5173` 或类似端口）。

在浏览器中访问前端 URL 以使用本应用。如果是首次运行，请使用初始超级用户凭据登录：
用户名: `admin`
密码: `changeme` (在生产环境中请务必修改此密码！)
