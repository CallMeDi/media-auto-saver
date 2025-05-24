# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import asyncio
import os
import shutil
from unittest import mock

from app.utils import db_utils # The module to test
from app.core.config import settings

# --- Fixtures ---

@pytest.fixture
def mock_settings_db_url(tmp_path, monkeypatch):
    """Mocks settings.DATABASE_URL to use a temporary path."""
    temp_db_file = tmp_path / "test.db"
    # Create a dummy db file for tests where it's expected to exist
    temp_db_file.touch()
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{temp_db_file}")
    return str(temp_db_file)

# --- Tests for export_database_to_sql ---

@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.os.path.exists", return_value=False)
async def test_export_db_file_not_exist(mock_os_exists, mock_settings_db_url):
    """Test export when database file does not exist."""
    result = await db_utils.export_database_to_sql("any_output.sql")
    assert result is False
    # os.path.exists should be called with the path from settings.DATABASE_URL
    db_path_from_settings = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    mock_os_exists.assert_called_once_with(db_path_from_settings)

@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.os.path.exists", return_value=True) # DB file exists
@mock.patch("app.utils.db_utils.shutil.which", return_value=None) # sqlite3 not found
async def test_export_sqlite3_not_found(mock_shutil_which, mock_os_exists, mock_settings_db_url):
    """Test export when sqlite3 command is not found."""
    result = await db_utils.export_database_to_sql("any_output.sql")
    assert result is False
    mock_shutil_which.assert_called_once_with("sqlite3")

@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.asyncio.create_subprocess_shell", new_callable=mock.AsyncMock)
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists", return_value=True) # DB and output file (during removal check)
@mock.patch("app.utils.db_utils.os.remove") # Mock os.remove for failure cases
@mock.patch("builtins.open", new_callable=mock.mock_open) # Mock open for writing output
async def test_export_successful(
    mock_open_file, mock_os_remove, mock_os_exists, mock_shutil_which,
    mock_subprocess_shell, tmp_path, mock_settings_db_url
):
    """Test successful database export."""
    mock_process = mock.AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = mock.AsyncMock(return_value=(b"", b"")) # stdout, stderr
    mock_subprocess_shell.return_value = mock_process
    
    output_sql_file = tmp_path / "exported_db.sql"
    result = await db_utils.export_database_to_sql(str(output_sql_file))

    assert result is True
    mock_open_file.assert_called_once_with(str(output_sql_file), "w", encoding="utf-8")
    mock_subprocess_shell.assert_called_once()
    mock_process.communicate.assert_awaited_once()
    mock_os_remove.assert_not_called() # Should not be called on success

@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.asyncio.create_subprocess_shell", new_callable=mock.AsyncMock)
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists") # Dynamic side effect for os.path.exists
@mock.patch("app.utils.db_utils.os.remove")
@mock.patch("builtins.open", new_callable=mock.mock_open)
async def test_export_fails_process_error(
    mock_open_file, mock_os_remove, mock_os_exists, mock_shutil_which,
    mock_subprocess_shell, tmp_path, mock_settings_db_url
):
    """Test export failure due to sqlite3 process error."""
    mock_process = mock.AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = mock.AsyncMock(return_value=(b"", b"Error dumping database"))
    mock_subprocess_shell.return_value = mock_process

    output_sql_file = tmp_path / "failed_export.sql"

    # os.path.exists needs to return True for db, then True for output file (to trigger remove)
    def os_exists_side_effect(path):
        if path == settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""):
            return True # DB exists
        if path == str(output_sql_file):
            return True # Output file was created (and needs removal)
        return False
    mock_os_exists.side_effect = os_exists_side_effect
    
    result = await db_utils.export_database_to_sql(str(output_sql_file))

    assert result is False
    mock_os_remove.assert_called_once_with(str(output_sql_file))

@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.asyncio.create_subprocess_shell", new_callable=mock.AsyncMock)
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists")
@mock.patch("app.utils.db_utils.os.remove")
@mock.patch("builtins.open", new_callable=mock.mock_open)
async def test_export_exception_during_process(
    mock_open_file, mock_os_remove, mock_os_exists, mock_shutil_which,
    mock_subprocess_shell, tmp_path, mock_settings_db_url
):
    """Test export failure due to an exception during subprocess execution."""
    mock_subprocess_shell.side_effect = Exception("Subprocess boom!")
    
    output_sql_file = tmp_path / "exception_export.sql"
    
    # os.path.exists needs to return True for db, then True for output file (to trigger remove)
    def os_exists_side_effect(path):
        if path == settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""):
            return True
        if path == str(output_sql_file): # Assume file might have been created before exception
            return True
        return False
    mock_os_exists.side_effect = os_exists_side_effect

    result = await db_utils.export_database_to_sql(str(output_sql_file))

    assert result is False
    mock_os_remove.assert_called_once_with(str(output_sql_file))


# --- Tests for import_database_from_sql ---

@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.os.path.exists", return_value=False) # SQL file does not exist
async def test_import_sql_file_not_exist(mock_os_exists, mock_settings_db_url):
    """Test import when SQL file does not exist."""
    sql_file_path = "non_existent_dump.sql"
    result = await db_utils.import_database_from_sql(sql_file_path)
    assert result is False
    mock_os_exists.assert_called_once_with(sql_file_path)


@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.os.path.exists", return_value=True) # SQL file exists
@mock.patch("app.utils.db_utils.shutil.which", return_value=None)   # sqlite3 not found
async def test_import_sqlite3_not_found(mock_shutil_which, mock_os_exists, mock_settings_db_url):
    """Test import when sqlite3 command is not found."""
    result = await db_utils.import_database_from_sql("dummy.sql")
    assert result is False
    mock_shutil_which.assert_called_once_with("sqlite3")


@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.os.remove", side_effect=Exception("Failed to delete!"))
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists") # Mock to control existence of SQL and DB files
async def test_import_fail_to_delete_existing_db(
    mock_os_exists, mock_shutil_which, mock_os_remove, tmp_path, mock_settings_db_url
):
    """Test import failure when existing database cannot be deleted."""
    sql_file = tmp_path / "dummy.sql"
    sql_file.touch() # Create dummy SQL file

    db_path_from_settings = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    def os_exists_side_effect(path):
        if path == str(sql_file): return True # SQL file exists
        if path == db_path_from_settings: return True # DB file exists (needs deletion)
        return False
    mock_os_exists.side_effect = os_exists_side_effect
    
    result = await db_utils.import_database_from_sql(str(sql_file))
    assert result is False
    mock_os_remove.assert_called_once_with(db_path_from_settings)


@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.asyncio.create_subprocess_shell", new_callable=mock.AsyncMock)
@mock.patch("app.utils.db_utils.os.remove") # Mock successful os.remove
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists")
async def test_import_successful(
    mock_os_exists, mock_shutil_which, mock_os_remove,
    mock_subprocess_shell, tmp_path, mock_settings_db_url
):
    """Test successful database import."""
    mock_process = mock.AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = mock.AsyncMock(return_value=(b"", b""))
    mock_subprocess_shell.return_value = mock_process

    sql_file = tmp_path / "import_me.sql"
    sql_file.touch()
    db_path_from_settings = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    def os_exists_side_effect(path):
        if path == str(sql_file): return True # SQL file exists
        if path == db_path_from_settings: return True # Old DB exists (will be removed)
        return False
    mock_os_exists.side_effect = os_exists_side_effect

    result = await db_utils.import_database_from_sql(str(sql_file))

    assert result is True
    mock_os_remove.assert_called_once_with(db_path_from_settings) # Verify old DB was removed
    mock_subprocess_shell.assert_called_once()
    mock_process.communicate.assert_awaited_once()


@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.asyncio.create_subprocess_shell", new_callable=mock.AsyncMock)
@mock.patch("app.utils.db_utils.os.remove")
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists", return_value=True) # SQL and DB files exist
async def test_import_fails_process_error(
    mock_os_exists, mock_shutil_which, mock_os_remove,
    mock_subprocess_shell, tmp_path, mock_settings_db_url
):
    """Test import failure due to sqlite3 process error."""
    mock_process = mock.AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = mock.AsyncMock(return_value=(b"", b"Error importing database"))
    mock_subprocess_shell.return_value = mock_process

    sql_file = tmp_path / "failed_import.sql"
    sql_file.touch()
    
    result = await db_utils.import_database_from_sql(str(sql_file))
    assert result is False


@pytest.mark.asyncio
@mock.patch("app.utils.db_utils.asyncio.create_subprocess_shell", new_callable=mock.AsyncMock)
@mock.patch("app.utils.db_utils.os.remove")
@mock.patch("app.utils.db_utils.shutil.which", return_value="/path/to/sqlite3")
@mock.patch("app.utils.db_utils.os.path.exists", return_value=True)
async def test_import_exception_during_process(
    mock_os_exists, mock_shutil_which, mock_os_remove,
    mock_subprocess_shell, tmp_path, mock_settings_db_url
):
    """Test import failure due to an exception during subprocess execution."""
    mock_subprocess_shell.side_effect = Exception("Subprocess import boom!")
    
    sql_file = tmp_path / "exception_import.sql"
    sql_file.touch()

    result = await db_utils.import_database_from_sql(str(sql_file))
    assert result is False

print("test_db_utils.py created with tests for database utility functions.")
