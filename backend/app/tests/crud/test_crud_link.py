# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import os
from unittest import mock
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link, LinkCreate, LinkUpdate, LinkStatus, LinkType
from app.crud.crud_link import CRUDLink, link as crud_link_instance # instance and class
# Assuming PROJECT_ROOT and USER_COOKIES_BASE_DIR_NAME are accessible for monkeypatching
# For PROJECT_ROOT, it's imported in crud_link.py from app.core.config, so we patch it there.
# For USER_COOKIES_BASE_DIR_NAME, it's a constant in crud_link.py.
from app.crud import crud_link as crud_link_module
from app.core.config import settings # To potentially access other settings if needed

# --- Fixtures ---

@pytest.fixture
def temp_cookie_structure(tmp_path: Path, monkeypatch) -> Path:
    """
    Creates a temporary directory structure for cookies and patches
    PROJECT_ROOT and USER_COOKIES_BASE_DIR_NAME for crud_link module.
    """
    project_root_mock = tmp_path / "project"
    project_root_mock.mkdir()

    user_cookies_base_name = "test_user_cookies"
    cookies_dir = project_root_mock / user_cookies_base_name
    cookies_dir.mkdir()

    # Patch the constants used in crud_link.py
    monkeypatch.setattr(crud_link_module, "PROJECT_ROOT", str(project_root_mock))
    monkeypatch.setattr(crud_link_module, "USER_COOKIES_BASE_DIR_NAME", user_cookies_base_name)
    
    return cookies_dir # Returns the path to the "test_user_cookies" directory

@pytest.fixture
async def test_link(db: AsyncSession) -> Link:
    """Fixture to create a basic link in the DB for update/fetch tests."""
    link_in = LinkCreate(url="http://initial.com", name="Initial Link")
    created_link = await crud_link_instance.create(db=db, obj_in=link_in)
    return created_link

# --- Tests for _validate_and_normalize_cookies_path ---
# This method is part of CRUDLink instance, not a static/module level function.
# We instantiate CRUDLink to test it.

@pytest.mark.parametrize(
    "user_path_input, mock_os_path_config, expected_output, expect_error",
    [
        # Valid cases
        ("my_cookie.txt", {"exists": True, "isfile": True, "isabs": False, "commonpath_match": True}, "my_cookie.txt", None),
        ("subdir/my_cookie.txt", {"exists": True, "isfile": True, "isabs": False, "commonpath_match": True}, os.path.join("subdir", "my_cookie.txt"), None),
        (None, {}, None, None), # Path is None

        # Invalid cases - ValueErrors
        ("/abs/path/cookie.txt", {"isabs": True}, None, ValueError), # Absolute path
        ("../secrets.txt", {"isabs": False, "normpath_traversal": True}, None, ValueError), # Directory traversal (normpath results in ..)
        ("outside_cookie.txt", {"exists": True, "isfile": True, "isabs": False, "commonpath_match": False}, None, ValueError), # Resolves outside base dir
        ("nonexistent.txt", {"exists": False, "isabs": False}, None, ValueError), # File does not exist
        ("is_a_dir", {"exists": True, "isfile": False, "isabs": False}, None, ValueError), # Path is a directory
    ]
)
def test_validate_and_normalize_cookies_path(
    user_path_input: Optional[str],
    mock_os_path_config: Dict[str, Any],
    expected_output: Optional[str],
    expect_error: Optional[type],
    temp_cookie_structure: Path # This sets up PROJECT_ROOT and USER_COOKIES_BASE_DIR_NAME
):
    crud_link_obj_for_test = CRUDLink(Link) # Instantiate to test the method

    # Path to the mocked USER_COOKIES_BASE_DIR_NAME
    cookies_base_dir_path = temp_cookie_structure

    # Create dummy files/dirs based on current param for os.path.exists/isfile if needed by the scenario
    if user_path_input and mock_os_path_config.get("exists"):
        full_mock_path = cookies_base_dir_path / user_path_input
        if not mock_os_path_config.get("isfile"): # if it's a dir
            full_mock_path.mkdir(parents=True, exist_ok=True)
        else: # if it's a file
            full_mock_path.parent.mkdir(parents=True, exist_ok=True)
            full_mock_path.touch()
            
    with mock.patch("os.path.exists", return_value=mock_os_path_config.get("exists", False)) as mock_exists, \
         mock.patch("os.path.isfile", return_value=mock_os_path_config.get("isfile", False)) as mock_isfile, \
         mock.patch("os.path.isabs", return_value=mock_os_path_config.get("isabs", False)) as mock_isabs, \
         mock.patch("os.path.normpath", side_effect=lambda p: os.path.normpath(p) if not mock_os_path_config.get("normpath_traversal") else "../" + p) as mock_normpath, \
         mock.patch("os.path.commonpath", side_effect=lambda paths: crud_link_module.PROJECT_ROOT if mock_os_path_config.get("commonpath_match") else "other_path") as mock_commonpath:

        # Configure side effect for os.path.exists based on actual path for more dynamic mock
        def dynamic_exists(path_arg):
            # Check if path_arg corresponds to the input file within the mocked structure
            if user_path_input and str(cookies_base_dir_path / user_path_input) in str(path_arg) :
                return mock_os_path_config.get("exists", False)
            return False # default for other paths
        mock_exists.side_effect = dynamic_exists

        if expect_error:
            with pytest.raises(expect_error):
                crud_link_obj_for_test._validate_and_normalize_cookies_path(user_path_input)
        else:
            result = crud_link_obj_for_test._validate_and_normalize_cookies_path(user_path_input)
            assert result == expected_output


# --- Tests for overridden create method ---

@pytest.mark.asyncio
async def test_create_link_with_valid_cookies_path(db: AsyncSession, temp_cookie_structure: Path):
    # Create a dummy cookie file
    cookie_file_path_relative = "user1/specific_cookie.txt"
    cookie_file_abs = temp_cookie_structure / cookie_file_path_relative
    cookie_file_abs.parent.mkdir(parents=True, exist_ok=True)
    cookie_file_abs.touch()

    link_in = LinkCreate(
        url="http://cookiepath.com",
        name="Cookie Path Link",
        cookies_path=cookie_file_path_relative # Relative path
    )
    # We are not mocking _validate_and_normalize_cookies_path here, letting it run with patched os.path
    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("os.path.isfile", return_value=True), \
         mock.patch("os.path.isabs", return_value=False), \
         mock.patch("os.path.commonpath", return_value=str(temp_cookie_structure.parent)): # mock commonpath to match project_root
        created_link = await crud_link_instance.create(db=db, obj_in=link_in)
    
    assert created_link.cookies_path == os.path.normpath(cookie_file_path_relative)

@pytest.mark.asyncio
async def test_create_link_cookies_path_none(db: AsyncSession):
    link_in = LinkCreate(url="http://nocookie.com", name="No Cookie Link", cookies_path=None)
    created_link = await crud_link_instance.create(db=db, obj_in=link_in)
    assert created_link.cookies_path is None

@pytest.mark.asyncio
async def test_create_link_invalid_cookies_path_value_error(db: AsyncSession, temp_cookie_structure: Path):
    link_in = LinkCreate(
        url="http://invalidcookie.com",
        name="Invalid Cookie Link",
        cookies_path="/absolute/path/not_allowed.txt" # This should cause _validate to fail
    )
    # Let _validate_and_normalize_cookies_path run, it should raise ValueError due to absolute path
    with mock.patch("os.path.isabs", return_value=True): # Mock isabs to trigger the error
        with pytest.raises(ValueError) as excinfo:
            await crud_link_instance.create(db=db, obj_in=link_in)
    assert "absolute path" in str(excinfo.value)


# --- Tests for overridden update method ---

@pytest.mark.asyncio
async def test_update_link_with_valid_cookies_path(db: AsyncSession, test_link: Link, temp_cookie_structure: Path):
    cookie_file_path_relative = "user2/updated_cookie.txt"
    cookie_file_abs = temp_cookie_structure / cookie_file_path_relative
    cookie_file_abs.parent.mkdir(parents=True, exist_ok=True)
    cookie_file_abs.touch()

    update_data = LinkUpdate(cookies_path=cookie_file_path_relative, name="Updated Name CP")
    
    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("os.path.isfile", return_value=True), \
         mock.patch("os.path.isabs", return_value=False), \
         mock.patch("os.path.commonpath", return_value=str(temp_cookie_structure.parent)):
        updated_link = await crud_link_instance.update(db=db, db_obj=test_link, obj_in=update_data)
    
    assert updated_link.cookies_path == os.path.normpath(cookie_file_path_relative)
    assert updated_link.name == "Updated Name CP"

@pytest.mark.asyncio
async def test_update_link_cookies_path_to_none(db: AsyncSession, test_link: Link, temp_cookie_structure: Path):
    # First, set a cookie path
    initial_cookie_file = "user_initial/cookie.txt"
    (temp_cookie_structure / initial_cookie_file).parent.mkdir(parents=True, exist_ok=True)
    (temp_cookie_structure / initial_cookie_file).touch()
    
    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("os.path.isfile", return_value=True), \
         mock.patch("os.path.isabs", return_value=False), \
         mock.patch("os.path.commonpath", return_value=str(temp_cookie_structure.parent)):
        link_with_cookie = await crud_link_instance.update(db=db, db_obj=test_link, obj_in=LinkUpdate(cookies_path=initial_cookie_file))
    assert link_with_cookie.cookies_path == initial_cookie_file

    # Now update to None
    update_to_none_data = LinkUpdate(cookies_path=None)
    updated_link_no_cookie = await crud_link_instance.update(db=db, db_obj=link_with_cookie, obj_in=update_to_none_data)
    assert updated_link_no_cookie.cookies_path is None

@pytest.mark.asyncio
async def test_update_link_invalid_cookies_path_value_error(db: AsyncSession, test_link: Link, temp_cookie_structure: Path):
    update_data = LinkUpdate(cookies_path="../attempt_traversal.txt")
    with mock.patch("os.path.normpath", return_value="../attempt_traversal.txt"): # Mock normpath to simulate traversal
        with pytest.raises(ValueError) as excinfo:
            await crud_link_instance.update(db=db, db_obj=test_link, obj_in=update_data)
    assert "directory traversal" in str(excinfo.value)


# --- Tests for get_by_url ---

@pytest.mark.asyncio
async def test_get_by_url_existing(db: AsyncSession):
    url = "http://getmebyurl.com"
    link_in = LinkCreate(url=url, name="Get Me By URL")
    created_link = await crud_link_instance.create(db=db, obj_in=link_in)
    
    fetched_link = await crud_link_instance.get_by_url(db=db, url=url)
    assert fetched_link is not None
    assert fetched_link.id == created_link.id
    assert fetched_link.url == url

@pytest.mark.asyncio
async def test_get_by_url_non_existent(db: AsyncSession):
    fetched_link = await crud_link_instance.get_by_url(db=db, url="http://nonexistenturl.com")
    assert fetched_link is None


# --- Tests for get_enabled_links ---

@pytest.mark.asyncio
async def test_get_enabled_links(db: AsyncSession):
    await crud_link_instance.create(db=db, obj_in=LinkCreate(url="http://enabled1.com", name="Enabled 1", is_enabled=True, link_type=LinkType.CREATOR))
    await crud_link_instance.create(db=db, obj_in=LinkCreate(url="http://disabled1.com", name="Disabled 1", is_enabled=False, link_type=LinkType.CREATOR))
    await crud_link_instance.create(db=db, obj_in=LinkCreate(url="http://enabled2.com", name="Enabled 2", is_enabled=True, link_type=LinkType.LIVE))
    await crud_link_instance.create(db=db, obj_in=LinkCreate(url="http://enabled3.com", name="Enabled 3", is_enabled=True, link_type=LinkType.CREATOR))

    # Test fetching all enabled links
    all_enabled = await crud_link_instance.get_enabled_links(db=db)
    assert len(all_enabled) == 3
    for link in all_enabled:
        assert link.is_enabled is True

    # Test filtering enabled links by type CREATOR
    creator_enabled = await crud_link_instance.get_enabled_links(db=db, link_type=LinkType.CREATOR)
    assert len(creator_enabled) == 2
    for link in creator_enabled:
        assert link.link_type == LinkType.CREATOR
        assert link.is_enabled is True
        assert link.url in ["http://enabled1.com", "http://enabled3.com"]

    # Test filtering enabled links by type LIVE
    live_enabled = await crud_link_instance.get_enabled_links(db=db, link_type=LinkType.LIVE)
    assert len(live_enabled) == 1
    assert live_enabled[0].link_type == LinkType.LIVE
    assert live_enabled[0].url == "http://enabled2.com"

    # Test when no enabled links match criteria
    other_type_enabled = await crud_link_instance.get_enabled_links(db=db, link_type=LinkType.OTHER)
    assert len(other_type_enabled) == 0


# --- Tests for update_status ---

@pytest.mark.asyncio
async def test_update_status(db: AsyncSession, test_link: Link):
    initial_updated_at = test_link.updated_at

    # 1. Test updating to IDLE with success
    await asyncio.sleep(0.01) # ensure time difference
    link_idle_success = await crud_link_instance.update_status(db=db, db_obj=test_link, status=LinkStatus.IDLE, is_success=True)
    assert link_idle_success.status == LinkStatus.IDLE
    assert link_idle_success.error_message is None
    assert link_idle_success.last_checked_at > test_link.last_checked_at if test_link.last_checked_at else True
    assert link_idle_success.last_success_at > test_link.last_success_at if test_link.last_success_at else True
    assert link_idle_success.updated_at > initial_updated_at
    
    prev_last_success_at = link_idle_success.last_success_at
    initial_updated_at = link_idle_success.updated_at # update for next check

    # 2. Test updating to DOWNLOADING (not success)
    await asyncio.sleep(0.01)
    link_downloading = await crud_link_instance.update_status(db=db, db_obj=link_idle_success, status=LinkStatus.DOWNLOADING, is_success=False)
    assert link_downloading.status == LinkStatus.DOWNLOADING
    assert link_downloading.error_message is None
    assert link_downloading.last_checked_at > link_idle_success.last_checked_at
    assert link_downloading.last_success_at == prev_last_success_at # Should not change
    assert link_downloading.updated_at > initial_updated_at
    initial_updated_at = link_downloading.updated_at

    # 3. Test updating to ERROR with an error message
    await asyncio.sleep(0.01)
    error_msg = "Download failed badly"
    link_error = await crud_link_instance.update_status(db=db, db_obj=link_downloading, status=LinkStatus.ERROR, error_message=error_msg, is_success=False)
    assert link_error.status == LinkStatus.ERROR
    assert link_error.error_message == error_msg
    assert link_error.last_checked_at > link_downloading.last_checked_at
    assert link_error.last_success_at == prev_last_success_at # Should not change
    assert link_error.updated_at > initial_updated_at

print("test_crud_link.py created with CRUD tests for Link.")
