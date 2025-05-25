<!-- Optional: Add a project logo or banner here -->
<!-- e.g., <p align="center"><img src="path/to/logo.png" alt="Media Auto Saver Logo" width="200"/></p> -->

# Media Auto Saver

[简体中文](README.zh-CN.md)

<p align="center">
  <!-- CI Status -->
  <a href="https://github.com/CallMeDi/media-auto-saver/actions/workflows/ci.yml"><img src="https://github.com/CallMeDi/media-auto-saver/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <!-- License -->
  <a href="LICENSE"><img src="https://img.shields.io/github/license/CallMeDi/media-auto-saver" alt="License"></a>
  <!-- Discord -->
  <a href="https://discord.gg/XBP8trYmyP"><img src="https://img.shields.io/discord/1158991319205019738?logo=discord&label=Discord&color=7289DA" alt="Discord"></a>
</p>

**Media Auto Saver** is your personal, automated media archiving assistant. It diligently downloads or records content from various websites based on links you provide, making it effortless to build a local archive of your favorite creators, series, or live streams. Set up your links and let Media Auto Saver handle the rest!

This open-source project is actively developed and welcomes contributions. Whether you're looking to add support for new sites, enhance existing features, or improve the user experience, we'd love to have your input. Join our community and help shape the future of Media Auto Saver!

💬 **Join the discussion and contribute on Discord: https://discord.gg/XBP8trYmyP**

## Table of Contents

- [Media Auto Saver](#media-auto-saver)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Screenshots](#screenshots)
  - [Technology Stack](#technology-stack)
  - [Setup and Installation](#setup-and-installation)
  - [Running the Application](#running-the-application)
  - [Contributing](#contributing)
  - [License](#license)
  - [Documentation & Community](#documentation--community)

## ✨ Features

*   **Flexible Link Management**: Easily add and manage links to your favorite creators (e.g., YouTube channels, Pixiv artists) or specific live streams.
*   **Automated Content Archiving**: Set up a schedule and let Media Auto Saver automatically monitor active links for new content.
*   **Versatile Downloading Power**: Leverages `yt-dlp` for a wide range of video/audio content and `gallery-dl` for image galleries and artist pages.
*   **Comprehensive Download History**: Keep track of all download activities, including successes, failures, and downloaded files.
*   **User-Friendly Web Interface**: A clean and modern Web UI (built with Vue.js) for managing links, viewing history, and adjusting settings.
*   **Secure User Authentication**: Protects your setup with JWT-based authentication and password management features (including password reset).
*   **Advanced Cookie Management**: Supports both global and link-specific cookie configurations for accessing sites that require login.
*   **Database Management**: Includes options to export and import the application database for backups or migration.
*   **Easy Configuration**: Primarily configured via a straightforward `.env` file for simple setup.
*   **Extensible & Open Source**: Built with a modular architecture, ready for community contributions and new features!

## 📸 Screenshots

*   Login Page  
    ![Login Page](/docs/images/WebUI/登录页面.PNG)
*   Link Page  
    ![Link Page](/docs/images/WebUI/链接页面.PNG)
*   Add Link  
    ![Add Link](/docs/images/WebUI/添加链接.PNG)
*   Settings Page  
    ![Settings Page](/docs/images/WebUI/设置页面.PNG)
*   History Page  
    ![History Page](/docs/images/WebUI/下载历史.PNG)

## 🛠️ Technology Stack

The project is built with a modern Python backend and a Vue.js frontend.

### Backend (Python)

*   **Python Version**: `3.13.3` (as specified in `.python-version`). Developed and tested with this version.
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) for high-performance web APIs.
*   **Database**: [SQLModel](https://sqlmodel.tiangolo.com/) for ORM, using SQLite with `aiosqlite` for asynchronous operations.
*   **Task Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/) for background job management.
*   **Media Downloaders**:
    *   `yt-dlp`: For video and audio content.
    *   `gallery-dl`: For image galleries and artist pages. (Note: `gallery-dl` CLI should be accessible).
*   **Authentication**: JWT tokens handled by `Passlib` and `python-jose`.
*   **Testing**:
    *   `pytest` for unit and integration tests.
    *   `pytest-cov` for code coverage.
    *   `pytest-asyncio` for asynchronous test support.
*   **Linting**: `Flake8` is used for code style checking.
*   **Server**: `Uvicorn` as the ASGI server.
*   *(See `backend/requirements.txt` for all production dependencies and `backend/requirements-dev.txt` for development tools.)*

### Frontend (Vue.js)

*   **Node.js Version**: LTS versions (e.g., 20.x or later) are recommended. (CI uses 20.x).
*   **Framework**: [Vue.js 3](https://vuejs.org/) (Composition API).
*   **Build Tool**: [Vite](https://vitejs.dev/) for fast development and optimized builds.
*   **State Management**: [Pinia](https://pinia.vuejs.org/).
*   **Routing**: [Vue Router](https://router.vuejs.org/).
*   **HTTP Client**: [Axios](https://axios-http.com/).
*   **UI Components**: [Element Plus](https://element-plus.org/).
*   **Testing**:
    *   `Vitest`: Unit and component testing framework.
    *   `@vue/test-utils`: For Vue component interaction in tests.
*   **Linting**: ESLint and Prettier (setup recommended, CI may enforce).
*   *(See `frontend/package.json` for all dependencies and development tools.)*

## 🚀 Setup and Installation

Follow these steps to get Media Auto Saver up and running on your local machine.

### Prerequisites

*   **Git**: For cloning the repository.
*   **Python**: Version `3.13.3` (see `.python-version`). A recent Python 3.10+ version should generally work.
*   **Node.js**: LTS version (e.g., 20.x or later, matching CI).
*   **npm** or **yarn**: For frontend package management.
*   (`Optional`) `gallery-dl` CLI tool: While the Python package might provide it, ensuring the command-line tool `gallery-dl` is independently installed and in your system's PATH can be beneficial for the media downloading features.

### 1. Clone the Repository

```bash
git clone https://github.com/CallMeDi/media-auto-saver.git
cd media-auto-saver
```

### 2. Backend Setup (Python)

*   **Navigate to backend directory:**
    ```bash
    cd backend
    ```
*   **(Recommended)** Create and activate a Python virtual environment:
    ```bash
    python3 -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```
*   **Install dependencies:**
    *   For running the application:
        ```bash
        pip install -r requirements.txt
        ```
    *   For development (e.g., running tests, linting):
        ```bash
        pip install -r requirements-dev.txt
        ```
*   **Configure Environment Variables:**
    *   Create a `.env` file in the `backend` directory. (e.g., `touch .env` or copy from a future `.env.example`).
    *   Edit `backend/.env` and add the following critical variable:
        ```env
        SECRET_KEY=your_strong_random_secret_key_here 
        # Example: openssl rand -hex 32
        ```
    *   You can also override other default settings in `backend/.env` if needed:
        ```env
        # INITIAL_SUPERUSER_USERNAME=admin
        # INITIAL_SUPERUSER_PASSWORD=changeme
        # DATABASE_URL=sqlite+aiosqlite:///./database.db  # Relative to backend directory
        # MEDIA_ROOT=../media  # Relative to backend directory
        # MAX_CONCURRENT_DOWNLOADS=5
        # LINK_MONITOR_INTERVAL_MINUTES=60
        # SITE_COOKIES_JSON='{"example.com": "path/to/cookies.txt"}'
        ```
        Refer to `backend/app/core/config.py` for all available settings and their default values. The paths for `DATABASE_URL` and `MEDIA_ROOT` in the example above are relative to the `backend` directory if you prefer that, or you can use absolute paths. By default, they are in the project root.
*   **Verify `gallery-dl` (if installed separately):**
    ```bash
    gallery-dl --version
    ```
*   **Return to the project root directory:**
    ```bash
    cd ..
    ```

### 3. Frontend Setup (Vue.js)

*   **Navigate to frontend directory:**
    ```bash
    cd frontend
    ```
*   **Install dependencies:**
    ```bash
    npm install
    # or yarn install
    ```
*   **Return to the project root directory (optional, for context):**
    ```bash
    cd ..
    ```

## ▶️ Running the Application

Once you have completed the setup and installation steps:

### 1. Run the Backend Server (FastAPI)

*   **Ensure you are in the project root directory (`media-auto-saver`).**
*   **Activate your Python virtual environment** (if you created one during setup):
    ```bash
    # On Linux/macOS:
    source backend/venv/bin/activate 
    # On Windows:
    # backend\venv\Scripts\activate
    ```
    *(Adjust path if your venv is named differently or located elsewhere relative to the project root)*
*   **Navigate to the backend directory and start the Uvicorn server:**
    ```bash
    cd backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
*   The backend API will now be accessible at `http://localhost:8000`.
*   Interactive API documentation (Swagger UI) is available at `http://localhost:8000/api/v1/docs`.

### 2. Run the Frontend Development Server (Vite)

*   **Open a new terminal window/tab.**
*   **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
*   **Start the Vite development server:**
    ```bash
    npm run dev
    # or yarn dev
    ```
*   The frontend UI will typically be accessible at `http://localhost:5173` (Vite will confirm the exact URL in the terminal).

### Accessing the Application

Open the frontend URL (e.g., `http://localhost:5173`) in your web browser.

*   **Default Superuser Credentials:**
    *   Username: `admin`
    *   Password: `changeme`
    *(These are the defaults if not overridden in your `backend/.env` file. It is strongly recommended to change the default password immediately via the "Settings" page after your first login, especially if deploying this application.)*

## 🐳 Docker Deployment

Deploying Media Auto Saver with Docker and Docker Compose simplifies setup and provides a consistent environment.

### Prerequisites

*   **Docker**: Install Docker from [Docker's official website](https://www.docker.com/get-started).
*   **Docker Compose**: Usually included with Docker Desktop. If not, follow the [Docker Compose installation guide](https://docs.docker.com/compose/install/).

### Configuration

1.  **Backend Environment File (`.env`)**:
    The backend service requires an environment file for configuration, primarily for the `SECRET_KEY`.
    *   Create a file named `.env` inside the `backend` directory at the project root: `media-auto-saver/backend/.env`.
    *   This file will be used by `docker-compose.yml`.
    *   Add your `SECRET_KEY` to this file. You can generate a strong key using `openssl rand -hex 32`.
        ```env
        # In media-auto-saver/backend/.env
        SECRET_KEY=your_very_strong_random_secret_key_for_docker_here
        ```
    *   You can also override other default settings from `backend/app/core/config.py` in this file if needed. For example:
        ```env
        # INITIAL_SUPERUSER_USERNAME=admin
        # INITIAL_SUPERUSER_PASSWORD=changeme
        ```
    *   **Important Note on Paths**: The default paths for `DATABASE_URL` (e.g., `sqlite+aiosqlite:///database.db`) and `MEDIA_ROOT` (e.g., `media`) defined in `backend/app/core/config.py` are relative to the application's root directory *inside the container* (`/app_code`). The `docker-compose.yml` file is already configured to map host directories (`./database.db`, `./media/`, `./user_cookies/` in your project root) to these expected locations within the container. Therefore, you typically **do not need** to redefine `DATABASE_URL` or `MEDIA_ROOT` in your `media-auto-saver/backend/.env` file unless you intend to change these paths *within the container structure*.

### Running with Docker Compose

1.  **Navigate to the project root directory** (`media-auto-saver`) in your terminal.
2.  **Build and start the services**:
    ```bash
    docker-compose up -d --build
    ```
    *   `--build`: This flag tells Docker Compose to build the images before starting the containers. It's good practice to include it if you've made changes to the Dockerfiles or application code.
    *   `-d` (detached mode): Runs the containers in the background.

### Accessing the Application

Once the containers are running:

*   **Frontend UI**: Open your browser and go to `http://localhost:5173`
*   **Backend API**: Accessible at `http://localhost:8000` (e.g., for API docs: `http://localhost:8000/api/v1/docs`)

### Data Persistence

The `docker-compose.yml` is configured to persist data on your host machine:

*   **Database**: The SQLite database file (`database.db`) will be stored in your project root directory (`media-auto-saver/database.db`).
*   **Media Files**: Downloaded media will be stored in `media-auto-saver/media/`.
*   **User Cookies**: Custom cookie files will be stored in `media-auto-saver/user_cookies/`.

This ensures your data remains even if you stop or remove the containers.

### Stopping the Application

To stop all running services defined in the `docker-compose.yml`:

1.  **Navigate to the project root directory** (`media-auto-saver`).
2.  **Run the command**:
    ```bash
    docker-compose down
    ```
    This will stop and remove the containers. Your persisted data (database, media files) will remain on your host machine.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

We welcome contributions of all types, from bug reports and feature requests to code enhancements and documentation improvements. Please refer to our [Contribution Guidelines](docs/CONTRIBUTING.en.md) for details on how to get started, including how to set up your development environment and run tests.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Documentation & Community

Want to dive deeper into the project or contribute? Check out these resources:

*   **Understanding the Project:**
    *   Architecture Overview: [中文](docs/ARCHITECTURE.zh-CN.md) | [English](docs/ARCHITECTURE.en.md)
    *   API Documentation: [中文](docs/API_DOCUMENTATION.zh-CN.md) | [English](docs/API_DOCUMENTATION.en.md)
*   **For Contributors:**
    *   Contribution Guidelines: [中文](docs/CONTRIBUTING.zh-CN.md) | [English](docs/CONTRIBUTING.en.md)

We encourage you to read these documents if you plan to contribute or want to understand the technical details.
