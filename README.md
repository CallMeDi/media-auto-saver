# Media Auto Saver

[简体中文](README.zh-CN.md)

Automatically download or record media from various websites based on added links.
This project is in its early stages and has many areas that need improvement and enhancement. **Contributors are very welcome**. And if you have interesting ideas for this project, feel free to discuss.

## Features

*   Add links to creators (e.g., YouTube channels, Pixiv artists) or live streams.
*   Automatically monitors enabled links based on a configurable schedule.
*   Downloads new media using `yt-dlp` for videos/audio and `gallery-dl` for images/galleries.
*   Keeps a history of download attempts (success/failure).
*   Web UI (Vue.js frontend) for managing links, viewing history, and configuration.
*   User authentication (JWT).
*   Password reset functionality.
*   Configurable via `.env` file.

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


## Dependencies

### Backend (Python)

*   Python 3.8+
*   See `backend/requirements.txt` for Python package dependencies (installed via pip). Key packages include:
    *   FastAPI
    *   SQLModel (with aiosqlite)
    *   Uvicorn
    *   APScheduler
    *   yt-dlp
    *   gallery-dl
    *   Passlib, python-jose
*   **External CLI Tool:** `gallery-dl` must be installed and accessible in your system's PATH. Installing the `gallery-dl` Python package via `requirements.txt` usually handles this.

### Frontend (Node.js)

*   Node.js (check `frontend/package.json` for version compatibility, likely LTS)
*   npm or yarn
*   See `frontend/package.json` for Node.js dependencies (installed via npm/yarn). Key packages include:
    *   Vue.js 3
    *   Vite
    *   Pinia
    *   Vue Router
    *   Axios

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd media-auto-saver
    ```

2.  **Backend Setup:**
    *   (Optional, Recommended) Create and activate a Python virtual environment:
        ```bash
        python3 -m venv venv
        source venv/bin/activate # On Linux/macOS
        # venv\Scripts\activate # On Windows
        ```
    *   Install backend dependencies:
        ```bash
        pip install -r backend/requirements.txt
        ```
    *   Verify `gallery-dl` command works:
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
    *   Go back to the project root:
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
    *   Make sure you are in the project root directory (`media-auto-saver`).
    *   If using a virtual environment, ensure it's activated.
    *   Start the server:
        ```bash
        cd backend
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
    *   The API will be available at `http://localhost:8000`.
    *   API documentation (Swagger UI) at `http://localhost:8000/api/v1/docs`.

2.  **Run the Frontend (Vue/Vite):**
    *   Open a *new* terminal.
    *   Navigate to the frontend directory:
        ```bash
        cd frontend
        ```
    *   Start the development server:
        ```bash
        npm run dev
        # or yarn dev
        ```
    *   The frontend UI will be available at the address shown in the terminal (usually `http://localhost:5173` or similar).

Access the frontend URL in your browser to use the application. Log in with the initial superuser credentials if it's the first run.
Username: admin
Password: changeme
