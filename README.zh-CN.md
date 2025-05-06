# 媒体自动保存器

根据添加的链接自动从各种网站下载或录制媒体。
这个项目处在起步阶段，有很多需要提升和改进的地方，**非常欢迎贡献者**。如果对于这个项目你有有趣的想法，欢迎讨论。

## 功能

*   添加创作者（例如，YouTube 频道、Pixiv 艺术家）或直播的链接。
*   根据可配置的计划自动监控启用的链接。
*   使用 `yt-dlp` 下载新的视频/音频媒体，使用 `gallery-dl` 下载图像/图库。
*   保留下载尝试的历史记录（成功/失败）。
*   用于管理链接、查看历史记录和配置的 Web UI (Vue.js 前端)。
*   用户认证 (JWT)。
*   密码重置功能。
*   可通过 `.env` 文件配置。

## 依赖项

### 后端 (Python)

*   Python 3.8+
*   请参阅 `backend/requirements.txt` 获取 Python 包依赖项（通过 pip 安装）。主要包包括：
    *   FastAPI
    *   SQLModel (with aiosqlite)
    *   Uvicorn
    *   APScheduler
    *   yt-dlp
    *   gallery-dl
    *   Passlib, python-jose
*   **外部 CLI 工具：** 必须安装 `gallery-dl` 并在系统 PATH 中可访问。通过 `requirements.txt` 安装 `gallery-dl` Python 包通常会处理此问题。

### 前端 (Node.js)

*   Node.js（检查 `frontend/package.json` 获取版本兼容性，可能是 LTS）
*   npm 或 yarn
*   请参阅 `frontend/package.json` 获取 Node.js 依赖项（通过 npm/yarn 安装）。主要包包括：
    *   Vue.js 3
    *   Vite
    *   Pinia
    *   Vue Router
    *   Axios

## 设置与安装

1.  **克隆仓库：**
    ```bash
    git clone <repository_url>
    cd media-auto-saver
    ```

2.  **后端设置：**
    *   （可选，推荐）创建并激活 Python 虚拟环境：
        ```bash
        python3 -m venv venv
        source venv/bin/activate # On Linux/macOS
        # venv\Scripts\activate # On Windows
        ```
    *   安装后端依赖项：
        ```bash
        pip install -r backend/requirements.txt
        ```
    *   验证 `gallery-dl` 命令是否工作：
        ```bash
        gallery-dl --version
        ```

3.  **前端设置：**
    *   导航到前端目录：
        ```bash
        cd frontend
        ```
    *   安装前端依赖项：
        ```bash
        npm install
        # or yarn install
        ```
    *   返回项目根目录：
        ```bash
        cd ..
        ```

## 运行应用程序

1.  **运行后端 (FastAPI)：**
    *   确保您位于项目根目录 (`media-auto-saver`)。
    *   如果使用虚拟环境，请确保已激活。
    *   启动服务器：
        ```bash
        cd backend
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   API 将在 `http://localhost:8000` 可用。
    *   API 文档 (Swagger UI) 在 `http://localhost:8000/api/v1/docs`。

2.  **运行前端 (Vue/Vite)：**
    *   打开一个**新**终端。
    *   导航到前端目录：
        ```bash
        cd frontend
        ```
    *   启动开发服务器：
        ```bash
        npm run dev
        # or yarn dev
        ```
    *   前端 UI 将在终端中显示的地址可用（通常是 `http://localhost:5173` 或类似地址）。

在浏览器中访问前端 URL 以使用应用程序。如果是首次运行，请使用初始超级用户凭据登录。
用户名: admin
密码: changeme