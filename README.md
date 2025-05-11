# Media Auto Saver

[简体中文](README.zh-CN.md)

Media Auto Saver is a powerful tool designed to automatically download or record media from various websites based on user-added links. Whether you want to archive content from your favorite creators or save live streams, this project aims to simplify the process.

As an early-stage open-source project, there's plenty of room for improvement and new features. We warmly welcome contributors of all levels! If you have exciting ideas or want to help enhance the project, please feel free to join the discussion and contribute.

## Table of Contents

- [Media Auto Saver](#media-auto-saver)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Examples](#examples)
  - [Documentation \& Community](#documentation--community)
  - [Technology Stack](#technology-stack)
    - [Backend (Python)](#backend-python)
    - [Frontend (Node.js)](#frontend-nodejs)
  - [Setup and Installation](#setup-and-installation)
  - [Running the Application](#running-the-application)

## Features

*   **Flexible Link Management**: Add links to creators (e.g., YouTube channels, Pixiv artists) or specific live streams.
*   **Automated Monitoring**: Automatically monitors enabled links based on a user-configurable schedule.
*   **Versatile Downloading**: Downloads new media using `yt-dlp` for videos/audio and `gallery-dl` for images/galleries.
*   **Download History**: Keeps a comprehensive history of all download attempts (both successes and failures).
*   **Web Interface**: A user-friendly Web UI (Vue.js frontend) for managing links, viewing history, and configuring settings.
*   **Secure Authentication**: User authentication implemented with JWT.
*   **Password Management**: Includes password reset functionality.
*   **Easy Configuration**: Configurable via a simple `.env` file.

## Examples

*   Login Page
    ![Login Page](/samples/images/WebUI/登录页面.PNG)
*   Link Page
    ![Link Page](/samples/images/WebUI/链接页面.PNG)
*   Add Link
    ![Add Link](/samples/images/WebUI/添加链接.PNG)
*   Settings Page
    ![Settings Page](/samples/images/WebUI/设置页面.PNG)
*   History Page
    ![History Page](/samples/images/WebUI/下载历史.PNG)

## Documentation & Community

Want to dive deeper into the project or contribute? Check out these resources:

*   **Understanding the Project:**
    *   Architecture Overview: [中文](ARCHITECTURE.md) | [English](ARCHITECTURE.en.md)
    *   API Documentation: [中文](API_DOCUMENTATION.md) | [English](API_DOCUMENTATION.en.md)
*   **For Contributors:**
    *   Contribution Guidelines: [中文](CONTRIBUTING.md) | [English](CONTRIBUTING.en.md)

We encourage you to read these documents if you plan to contribute or want to understand the technical details.

## Technology Stack

### Backend (Python)

*   **Python Version**: 3.8+
*   **Key Packages**: (See `backend/requirements.txt` for a full list)
    *   FastAPI (for the web framework)
    *   SQLModel (ORM, with aiosqlite for async SQLite)
    *   Uvicorn (ASGI server)
    *   APScheduler (for background task scheduling)
    *   yt-dlp (for video/audio downloading)
    *   gallery-dl (for image/gallery downloading)
    *   Passlib, python-jose (for authentication and JWT)
*   **External CLI Tool**: `gallery-dl` must be installed and accessible in your system's PATH. (Installing the `gallery-dl` Python package via `requirements.txt` usually handles this).

### Frontend (Node.js)

*   **Node.js Version**: Check `frontend/package.json` for compatibility (LTS recommended).
*   **Package Manager**: npm or yarn
*   **Key Packages**: (See `frontend/package.json` for a full list)
    *   Vue.js 3 (core frontend framework)
    *   Vite (build tool and dev server)
    *   Pinia (state management)
    *   Vue Router (routing)
    *   Axios (HTTP client)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd media-auto-saver
    ```

2.  **Backend Setup:**
    *   (Recommended) Create and activate a Python virtual environment:
        ```bash
        python3 -m venv venv
        source venv/bin/activate # On Linux/macOS
        # venv\Scripts\activate # On Windows
        ```
    *   Install backend dependencies:
        ```bash
        pip install -r backend/requirements.txt
        ```
    *   Verify `gallery-dl` command is working:
        ```bash
        gallery-dl --version
        ```

3.  **Frontend Setup:**
    *   Navigate to the frontend directory:
        ```bash
        cd frontend
        ```
    *   Install frontend dependencies:
        ```bash
        npm install
        # or yarn install
        ```
    *   Return to the project root directory:
        ```bash
        cd ..
        ```

<!--
## Configuration

1.  **Copy the example environment file:**
    ```bash
    # If .env doesn't exist, create it from scratch or copy if an example exists
    # cp .env.example .env # Assuming an example file exists
    ```
    *Note: An example file wasn't provided, so create `.env` manually if needed.*

2.  **Edit the `.env` file** in the project root directory:
    *   `SECRET_KEY`: **Required** for JWT authentication. Generate a strong secret key (e.g., using `openssl rand -hex 32`). The existing one is for example purposes only.
    *   `DATABASE_URL`: Defaults to `sqlite+aiosqlite:///./database.db` in the project root. Change if needed.
    *   `MEDIA_ROOT`: Defaults to `./media` in the project root. Change where downloaded files should be stored.
    *   `INITIAL_SUPERUSER_USERNAME`, `INITIAL_SUPERUSER_PASSWORD`, `INITIAL_SUPERUSER_EMAIL`: Set credentials for the first admin user created on startup if no superuser exists. **Strongly recommended** to set these, especially the password (default is 'changeme').
    *   `LINK_MONITOR_INTERVAL_MINUTES`: How often the scheduler checks links (default: 60).
    *   `MAX_CONCURRENT_DOWNLOADS`: Maximum parallel download tasks (default: 5).
    *   `SITE_COOKIES_JSON`: (Optional) JSON string mapping lowercase site names to cookie file paths for global cookies (e.g., `{"pixiv": "/path/to/pixiv_cookies.txt"}`).
 -->

## Running the Application

1.  **Run the Backend (FastAPI):**
    *   Ensure you are in the project root directory (`media-auto-saver`).
    *   If using a Python virtual environment, make sure it's activated.
    *   Start the Uvicorn server:
        ```bash
        cd backend
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   The API will be accessible at `http://localhost:8000`.
    *   Interactive API documentation (Swagger UI) is available at `http://localhost:8000/api/v1/docs`.

2.  **Run the Frontend (Vue/Vite):**
    *   Open a *new* terminal window.
    *   Navigate to the frontend directory:
        ```bash
        cd frontend
        ```
    *   Start the Vite development server:
        ```bash
        npm run dev
        # or yarn dev
        ```
    *   The frontend UI will be accessible at the address shown in your terminal (usually `http://localhost:5173` or a similar port).

Access the frontend URL in your browser to use the application. If it's your first time running the app, log in with the initial superuser credentials:
Username: `admin`
Password: `changeme` (Please change this in a production environment!)
