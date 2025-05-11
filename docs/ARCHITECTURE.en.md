# Media Auto Saver Architecture Document

This document outlines the technical architecture of the Media Auto Saver project, including the backend, frontend, and their interactions.

## Table of Contents

- [Media Auto Saver Architecture Document](#media-auto-saver-architecture-document)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Technology Stack](#technology-stack)
  - [Backend Architecture](#backend-architecture)
    - [Main Backend Components](#main-backend-components)
    - [Backend Directory Structure (backend/app)](#backend-directory-structure-backendapp)
    - [Database](#database)
    - [Background Tasks and Scheduling](#background-tasks-and-scheduling)
    - [External Tool Integration](#external-tool-integration)
  - [Frontend Architecture](#frontend-architecture)
    - [Main Frontend Components](#main-frontend-components)
    - [Frontend Directory Structure (frontend/src)](#frontend-directory-structure-frontendsrc)
    - [State Management](#state-management)
    - [Routing](#routing)
  - [Frontend-Backend Interaction](#frontend-backend-interaction)
    - [API](#api)
    - [Authentication Mechanism](#authentication-mechanism)
  - [Data Flow Examples](#data-flow-examples)
    - [User Adds a New Link](#user-adds-a-new-link)
    - [Automatic Monitoring and Downloading](#automatic-monitoring-and-downloading)
  - [Potential Future Improvements](#potential-future-improvements)

## Overview

Media Auto Saver is a full-stack web application designed to automatically download media content from various websites. It consists of a Python FastAPI backend and a Vue.js frontend.

- **Backend**: Responsible for handling business logic, API requests, database interactions, user authentication, and monitoring and downloading media via scheduled tasks.
- **Frontend**: Provides the user interface, allowing users to manage links, view download history, configure settings, and interact with the backend API.

## Technology Stack

- **Backend**:
  - Language: Python 3.8+
  - Web Framework: FastAPI
  - Database: SQLite (via SQLModel ORM)
  - Async Task Scheduling: APScheduler
  - Media Downloaders: `yt-dlp`, `gallery-dl` (invoked as external CLI tools)
  - Authentication: JWT (JSON Web Tokens)
  - Server: Uvicorn
- **Frontend**:
  - Framework: Vue.js 3
  - Build Tool: Vite
  - State Management: Pinia
  - HTTP Client: Axios
  - Routing: Vue Router
  - UI Component Library: (Currently custom components; could consider introducing libraries like Vuetify, Element Plus in the future)

## Backend Architecture

The backend is built with FastAPI, a modern, fast (high-performance) Python web framework for building APIs.

### Main Backend Components

1.  **API Endpoints**: Define the HTTP interfaces accessible by clients for handling user requests, link management, history viewing, etc.
2.  **Business Logic Layer (Services/CRUD)**: Contains the core business logic, such as how to process links, trigger downloads, and manage users.
3.  **Data Access Layer (Models/CRUD/DB)**: Responsible for interacting with the database, including data model definitions (SQLModel) and CRUD operations.
4.  **Core Components (Core)**: Includes configuration management, security-related functions (e.g., password hashing, JWT generation/validation), and logging configuration.
5.  **Background Tasks (Tasks)**: Tasks executed periodically using APScheduler, primarily for monitoring enabled links and triggering the download process.

### Backend Directory Structure (backend/app)

-   `api/`: Contains API route definitions.
    -   `deps.py`: API dependencies, e.g., getting the current user.
    -   `v1/`: API version 1.
        -   `api.py`: Aggregates all v1 API routers.
        -   `endpoints/`: Contains specific API route implementations for various features (e.g., `links.py`, `users.py`).
-   `core/`: Core configuration and security modules.
    -   `config.py`: Application configuration management (loaded from environment variables).
    -   `logging_config.py`: Logging configuration.
    -   `security.py`: Password hashing, JWT token handling, etc.
-   `crud/`: Create, Read, Update, Delete (CRUD) operations.
    -   `crud_link.py`, `crud_user.py`, etc.: CRUD functions for specific data models.
-   `db/`: Database connection and session management.
    -   `session.py`: Database engine and session creation.
-   `models/`: SQLModel data model definitions (corresponding to database table structures).
    -   `link.py`, `user.py`, `history.py`, etc.
-   `schemas/`: Pydantic data models used for API request/response data validation and serialization.
    -   `token.py`: JWT token-related schemas.
    -   (Other schemas usually correspond to `models` but are used for API interaction)
-   `services/`: Higher-level business logic, may call CRUD operations and external services.
    -   `downloader.py`: Encapsulates the download logic for `yt-dlp` and `gallery-dl`.
-   `tasks/`: Background task definitions.
    -   `link_monitor.py`: Task for monitoring links and triggering downloads.
    -   `scheduler.py`: APScheduler configuration and startup.
-   `tests/`: Unit and integration tests.
-   `utils/`: Utility functions.
-   `main.py`: FastAPI application instance creation and main configuration.

### Database

-   Uses SQLite by default (database file `database.db` stored in the project root).
-   SQLModel is used for ORM functionality, combining the advantages of Pydantic and SQLAlchemy for convenient data model definition and database interaction.
-   Database tables include: users, links, history, password_resets, etc.

### Background Tasks and Scheduling

-   APScheduler is used for periodically executing background tasks.
-   The main task is `link_monitor`, which:
    1.  Fetches all enabled links from the database.
    2.  Checks each link for new media content.
    3.  If new content is found, calls the `downloader` service to download it.
    4.  Updates the download history.
-   The task execution frequency can be configured in the `.env` file (`LINK_MONITOR_INTERVAL_MINUTES`).

### External Tool Integration

-   `yt-dlp`: Used for downloading video and audio content.
-   `gallery-dl`: Used for downloading images and galleries.
-   These tools are invoked via `subprocess` in the backend. The `downloader.py` service encapsulates the logic for calling these tools.

## Frontend Architecture

The frontend is built with Vue.js 3, using Vite as the development and build tool, providing a modern development experience.

### Main Frontend Components

1.  **Views**: Represent different pages in the application (e.g., Login page, Links management page, History page).
2.  **Components**: Reusable UI elements (e.g., dialogs, form elements).
3.  **Layouts**: Define the overall structure and layout of pages.
4.  **Router**: Manages application navigation and view switching.
5.  **Store (Pinia)**: Manages the application's state centrally.

### Frontend Directory Structure (frontend/src)

-   `App.vue`: The root component of the Vue application.
-   `main.js`: The application's entry point, initializing the Vue instance, router, Pinia, etc.
-   `style.css`: Global CSS styles.
-   `assets/`: Static assets like images, fonts, etc.
-   `components/`: Reusable Vue components.
    -   `LinkDialog.vue`: Dialog for adding/editing links.
-   `layouts/`: Layout components.
    -   `DefaultLayout.vue`: The main layout for the application, possibly including a navigation bar, footer, etc.
-   `router/`: Vue Router configuration.
    -   `index.js`: Defines routing rules and navigation guards.
-   `stores/`: Pinia state management modules.
    -   `auth.js`: Manages user authentication state and tokens.
    -   `link.js`: Manages link-related data and operations.
    -   `history.js`: Manages history-related data.
    -   `error.js`: Manages global error state.
-   `utils/`: Utility functions or constants.
    -   `constants.js`: Constants used in the application.
-   `views/`: Page-level Vue components.
    -   `LoginView.vue`, `LinksView.vue`, `HistoryView.vue`, etc.

### State Management

-   Pinia is used for global state management.
-   Different store modules (e.g., `auth.js`, `link.js`) are responsible for managing the state of different parts of the application.
-   Components can access and modify shared state through Pinia stores, enabling communication and data synchronization between components.

### Routing

-   Vue Router is used for client-side routing in the Single Page Application (SPA).
-   The `router/index.js` file defines the application's route table, mapping URL paths to corresponding view components.
-   May include navigation guards to handle logic for pages requiring login, for example.

## Frontend-Backend Interaction

### API

-   The frontend communicates with the backend FastAPI-provided RESTful API via HTTP requests.
-   The base path for API endpoints is typically `/api/v1/`.
-   Backend API documentation (Swagger UI) is available at `/api/v1/docs` after starting the backend service, providing detailed information and testing capabilities for all available endpoints.

### Authentication Mechanism

-   User authentication is implemented using JWT (JSON Web Tokens).
-   **Login Flow**:
    1.  User enters username and password in the frontend.
    2.  Frontend sends credentials to the backend's `/api/v1/login/access-token` endpoint.
    3.  Backend validates credentials; if successful, generates a JWT and returns it to the frontend.
    4.  Frontend stores the JWT (usually in localStorage or sessionStorage) and includes it in subsequent API requests via the `Authorization` HTTP header (Bearer Token).
-   **Protected Endpoints**: Most backend API endpoints require a valid JWT for authentication. FastAPI's dependency injection system is used to validate tokens and get the current user.

## Data Flow Examples

### User Adds a New Link

1.  **Frontend**: User clicks the "Add Link" button on the `LinksView.vue` page, opening `LinkDialog.vue`.
2.  **Frontend**: User fills in link information (URL, name, type, etc.) and submits.
3.  **Frontend**: An action in the `link.js` store is called, sending a POST request via Axios to the backend `/api/v1/links/` endpoint with the link data in the request body.
4.  **Backend**: The corresponding API endpoint in `links.py` receives the request.
5.  **Backend**: Request data is validated using a Pydantic schema.
6.  **Backend**: A function in `crud_link.py` is called to save the new link data to the database.
7.  **Backend**: Returns a success response (usually containing the newly created link object) to the frontend.
8.  **Frontend**: The `link.js` store updates its state, and `LinksView.vue` re-renders to display the new link.

### Automatic Monitoring and Downloading

1.  **Backend (APScheduler)**: A scheduled task configured in `scheduler.py` triggers the monitoring function in `link_monitor.py`.
2.  **Backend**: `link_monitor` fetches all enabled links from the database (`crud_link.py`).
3.  **Backend**: For each link, appropriate logic (possibly in `link_utils.py` or `downloader.py`) is called to check for new media.
    - This might involve calling `yt-dlp --dump-json` or similar commands to get metadata without actual downloading, or comparing a list of already downloaded items with the remote list.
4.  **Backend**: If new media is detected, the download function in `downloader.py` is called.
5.  **Backend (`downloader.py`)**:
    -   Selects `yt-dlp` or `gallery-dl` based on the link type.
    -   Constructs the appropriate CLI command.
    -   Executes the download command using `subprocess`.
    -   Media files are saved to the `MEDIA_ROOT` directory configured in `.env`.
6.  **Backend**: After download completion, the `history` table is updated (`crud_history.py`) to record the download status (success/failure) and related information.
7.  **Frontend (Optional)**: Users can view the latest download history on the `HistoryView.vue` page, which fetches data from the backend `/api/v1/history/` endpoint.

## Potential Future Improvements

-   **More granular error handling and retry mechanisms**: Especially during the download process.
-   **Plugin system**: To allow users to add support for new websites or downloaders.
-   **WebSockets**: For real-time updates to the frontend (e.g., download progress).
-   **More comprehensive testing**: Increase coverage for unit and end-to-end tests.
-   **Containerization**: Using Docker for deployment.
-   **Introduction of a UI component library**: To improve frontend development efficiency and UI consistency.

This document aims to provide a high-level architectural overview. For more detailed information on specific modules or features, please refer to the source code and relevant comments.
