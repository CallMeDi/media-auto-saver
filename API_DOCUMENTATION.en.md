# Media Auto Saver API Documentation

This document provides detailed information about the Media Auto Saver backend API. The base path for all API endpoints is `/api/v1`.

**Note**: More detailed and interactive API documentation can be obtained by accessing `http://localhost:8000/api/v1/docs` (Swagger UI) or `http://localhost:8000/api/v1/redoc` (ReDoc) after running the backend service locally.

## Table of Contents

- [Authentication](#authentication)
- [User Management (Users)](#user-management-users)
- [Login](#login)
- [Password Reset](#password-reset)
- [Link Management (Links)](#link-management-links)
- [Download History (History)](#download-history-history)
- [Settings](#settings)
- [Database Management (Database)](#database-management-database)
- [Common Response Formats](#common-response-formats)
- [Error Handling](#error-handling)

## Authentication

Most API endpoints require authentication via JWT (JSON Web Token). After a successful login, the client receives an `access_token`. The client should include this token in the `Authorization` HTTP header of subsequent requests, formatted as `Bearer <access_token>`.

## User Management (Users)

Base path: `/users`

### `POST /users/`
- **Description**: Creates a new user (typically an admin operation, or open registration during initial setup).
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "username": "newuser"
    // "is_active": true, (optional, defaults to true)
    // "is_superuser": false (optional, defaults to false)
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "username": "newuser",
    "is_active": true,
    "is_superuser": false
  }
  ```
- **Authentication Required**: Yes (typically superuser privileges)

### `GET /users/me`
- **Description**: Gets information for the currently authenticated user.
- **Success Response (200 OK)**: (Same as above, returns current user information)
- **Authentication Required**: Yes

### `PUT /users/me`
- **Description**: Updates information for the currently authenticated user (e.g., email, password).
- **Request Body**:
  ```json
  {
    "email": "new_email@example.com", // optional
    "password": "new_secure_password", // optional
    "username": "current_username" // optional
  }
  ```
- **Success Response (200 OK)**: (Returns updated user information)
- **Authentication Required**: Yes

### `GET /users/{user_id}`
- **Description**: Gets information for a user with the specified ID (typically an admin operation).
- **Path Parameter**: `user_id` (integer)
- **Success Response (200 OK)**: (Returns specified user information)
- **Authentication Required**: Yes (typically superuser privileges)

### `PUT /users/{user_id}`
- **Description**: Updates information for a user with the specified ID (typically an admin operation).
- **Path Parameter**: `user_id` (integer)
- **Request Body**: (Same as `POST /users/`, but for updates)
- **Success Response (200 OK)**: (Returns updated user information)
- **Authentication Required**: Yes (typically superuser privileges)

## Login

Base path: `/login`

### `POST /login/access-token`
- **Description**: User login to obtain a JWT access token.
- **Request Body (form data)**:
  - `username`: User's username or email
  - `password`: User's password
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "your_jwt_token_here",
    "token_type": "bearer"
  }
  ```
- **Authentication Required**: No

### `POST /login/test-token`
- **Description**: Tests if the provided access token is valid.
- **Success Response (200 OK)**: (Returns user information corresponding to the current token)
- **Authentication Required**: Yes

## Password Reset

Base path: `/password-reset`

### `POST /password-reset/request-reset`
- **Description**: Requests a password reset. The backend typically generates a reset token and sends it to the user via email (if email service is configured).
- **Request Body**:
  ```json
  {
    "email": "user_to_reset@example.com"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "msg": "Password reset email sent" // Or similar message
  }
  ```
- **Authentication Required**: No

### `POST /password-reset/reset`
- **Description**: Sets a new password using a valid reset token.
- **Request Body**:
  ```json
  {
    "token": "valid_reset_token_here",
    "new_password": "new_strong_password"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "msg": "Password updated successfully"
  }
  ```
- **Authentication Required**: No

## Link Management (Links)

Base path: `/links`

### `POST /links/`
- **Description**: Adds a new media link.
- **Request Body**:
  ```json
  {
    "url": "https://www.youtube.com/channel/...",
    "name": "My Favorite Channel",
    "type": "youtube_channel", // e.g., youtube_channel, pixiv_user, generic_video, generic_gallery
    "is_enabled": true,
    "download_automatically": true,
    "tags": ["tag1", "tag2"], // optional
    "cookies": "{ \"cookie_name\": \"cookie_value\" }" // optional, JSON string for specific cookies
  }
  ```
- **Success Response (200 OK)**: (Returns the created link object, including `id`)
- **Authentication Required**: Yes

### `GET /links/`
- **Description**: Gets a list of all links, supports pagination.
- **Query Parameters**:
  - `skip` (integer, optional, default: 0): Number of records to skip.
  - `limit` (integer, optional, default: 100): Maximum number of records to return.
- **Success Response (200 OK)**: (Returns a list of link objects)
- **Authentication Required**: Yes

### `GET /links/{link_id}`
- **Description**: Gets information for a link with the specified ID.
- **Path Parameter**: `link_id` (integer)
- **Success Response (200 OK)**: (Returns the specified link object)
- **Authentication Required**: Yes

### `PUT /links/{link_id}`
- **Description**: Updates information for a link with the specified ID.
- **Path Parameter**: `link_id` (integer)
- **Request Body**: (Same as `POST /links/`, but for updates)
- **Success Response (200 OK)**: (Returns the updated link object)
- **Authentication Required**: Yes

### `DELETE /links/{link_id}`
- **Description**: Deletes a link with the specified ID.
- **Path Parameter**: `link_id` (integer)
- **Success Response (200 OK)**: (Returns the deleted link object or a confirmation message)
- **Authentication Required**: Yes

### `POST /links/{link_id}/trigger-download`
- **Description**: Manually triggers a download check for the specified link.
- **Path Parameter**: `link_id` (integer)
- **Success Response (200 OK)**:
  ```json
  {
    "msg": "Download triggered for link X"
  }
  ```
- **Authentication Required**: Yes

## Download History (History)

Base path: `/history`

### `GET /history/`
- **Description**: Gets download history records, supports pagination and filtering.
- **Query Parameters**:
  - `skip` (integer, optional, default: 0)
  - `limit` (integer, optional, default: 100)
  - `link_id` (integer, optional): Filter by link ID.
  - `status` (string, optional): Filter by download status (e.g., "success", "failure").
- **Success Response (200 OK)**: (Returns a list of history record objects)
  ```json
  // Example single history record object
  {
    "id": 1,
    "link_id": 1,
    "link_name": "My Favorite Channel",
    "timestamp": "2023-10-27T10:30:00Z",
    "status": "success",
    "message": "Downloaded 3 new items.",
    "downloaded_files": ["file1.mp4", "file2.jpg"] // List of actual downloaded files
  }
  ```
- **Authentication Required**: Yes

### `GET /history/{history_id}`
- **Description**: Gets a download history record with the specified ID.
- **Path Parameter**: `history_id` (integer)
- **Success Response (200 OK)**: (Returns the specified history record object)
- **Authentication Required**: Yes

## Settings

Base path: `/settings`

### `GET /settings/`
- **Description**: Gets current application settings.
- **Success Response (200 OK)**:
  ```json
  {
    "link_monitor_interval_minutes": 60,
    "max_concurrent_downloads": 5,
    "media_root": "/path/to/media",
    "site_cookies_json": "{\"pixiv\": \"/path/to/pixiv_cookies.txt\"}" // Example
    // Other configurable items
  }
  ```
- **Authentication Required**: Yes (typically superuser privileges)

### `PUT /settings/`
- **Description**: Updates application settings.
- **Request Body**: (Same structure as `GET /settings/` response, but for updates)
- **Success Response (200 OK)**: (Returns the updated settings object)
- **Authentication Required**: Yes (typically superuser privileges)

## Database Management (Database)

Base path: `/database`

These endpoints are for database import and export. Use with caution, especially the import operation which will overwrite existing data.

### `GET /database/export`
- **Description**: Exports the entire database as an SQL file and provides it for download.
- **Response Type**: `application/sql` (file download)
- **Success Response**: Direct download of an SQL file named `media_auto_saver_backup_YYYYMMDD_HHMMSS.sql`.
- **Authentication Required**: Yes (active user privileges required)

### `POST /database/import`
- **Description**: Uploads an SQL file and imports the database. **Warning: This operation will overwrite the current database!** The import process runs in the background.
- **Request Body (form data)**:
  - `file`: Required, the `.sql` file to upload.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Database import process started in the background. The application might restart or become temporarily unavailable. Please check server logs for status."
  }
  ```
- **Authentication Required**: Yes (active user privileges required)
- **Notes**:
  - Only `.sql` files are accepted.
  - The import operation may cause the application to be temporarily unavailable or require a restart.

## Common Response Formats

- Successful requests usually return `200 OK` or `201 Created` (for `POST` creating a resource).
- Response bodies are typically in JSON format.

## Error Handling

- **400 Bad Request**: Invalid request (e.g., missing required parameters, incorrect parameter format). The response body usually contains detailed error information.
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
- **401 Unauthorized**: No valid authentication token provided, or the token is invalid/expired.
  ```json
  {
    "detail": "Not authenticated"
  }
  ```
- **403 Forbidden**: The user is authenticated but does not have permission to perform the action.
  ```json
  {
    "detail": "The user doesn't have enough privileges"
  }
  ```
- **404 Not Found**: The requested resource does not exist.
  ```json
  {
    "detail": "Item not found"
  }
  ```
- **422 Unprocessable Entity**: The request body is correctly formatted but contains semantic errors (FastAPI often uses this for Pydantic validation failures).
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
- **500 Internal Server Error**: An unknown error occurred on the server side.
