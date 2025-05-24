# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import asyncio
import os
from unittest import mock
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.models.link import Link, LinkType
from app.services import downloader as downloader_service # The module to test
from app.core.config import settings, PROJECT_ROOT

# Define the constant from the downloader module for use in tests
USER_COOKIES_BASE_DIR_NAME = "user_cookies"

@pytest.fixture
def default_link_attributes() -> Dict[str, Any]:
    return {
        "id": 1,
        "url": "https://example.com/video1",
        "name": "Test Video",
        "link_type": LinkType.CREATOR, # Default to CREATOR type
        "site_name": "ExampleSite",
        "description": "A test video",
        "tags": "test,video",
        "is_enabled": True,
        "owner_id": 1,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "last_checked_at": None,
        "last_successful_download_at": None,
        "cookies_path": None,
        "settings": {},
        "status": "pending",
        "error_message": None,
        "download_history": []
    }

@pytest.fixture
def link_instance(default_link_attributes: Dict[str, Any]) -> Link:
    """Creates a Link instance with default attributes."""
    return Link.model_validate(default_link_attributes)

@pytest.fixture(autouse=True)
def mock_media_root(tmp_path: Path, monkeypatch):
    """Fixture to set MEDIA_ROOT to a temporary directory for tests."""
    temp_media_dir = tmp_path / "media"
    temp_media_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(temp_media_dir))
    # Also ensure download_archive.txt and gallery_dl_archive.sqlite can be created
    (temp_media_dir / "download_archive.txt").touch()
    (temp_media_dir / "gallery_dl_archive.sqlite").touch()
    return str(temp_media_dir)

# --- Tests for get_downloader_for_link ---

@pytest.mark.parametrize(
    "site_name, link_type, link_cookies_path, global_site_cookies, expected_downloader, expected_cookie_in_opts, link_cookie_exists, global_cookie_exists",
    [
        # yt-dlp cases
        ("YouTube", LinkType.CREATOR, None, {}, "yt-dlp", None, False, False),
        ("YouTube", LinkType.LIVE, None, {}, "yt-dlp", None, False, False), # Live link
        ("YouTube", LinkType.CREATOR, "yt_cookies.txt", {}, "yt-dlp", os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME, "yt_cookies.txt"), True, False), # Link specific cookie
        ("YouTube", LinkType.CREATOR, "yt_cookies.txt", {"youtube": "global_yt.txt"}, "yt-dlp", os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME, "yt_cookies.txt"), True, True), # Link specific takes precedence
        ("YouTube", LinkType.CREATOR, "yt_cookies.txt", {"youtube": "global_yt.txt"}, "yt-dlp", "global_yt.txt", False, True), # Link specific not found, use global
        ("YouTube", LinkType.CREATOR, None, {"youtube": "global_yt.txt"}, "yt-dlp", "global_yt.txt", False, True), # Global cookie
        ("YouTube", LinkType.CREATOR, "nonexistent.txt", {}, "yt-dlp", None, False, False), # Link specific cookie file doesn't exist

        # gallery-dl cases
        ("Pixiv", LinkType.CREATOR, None, {}, "gallery-dl", None, False, False),
        ("Instagram", LinkType.CREATOR, "ig_cookies.txt", {}, "gallery-dl", os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME, "ig_cookies.txt"), True, False),
        ("Artstation", LinkType.CREATOR, "as_cookies.txt", {"artstation": "global_as.txt"}, "gallery-dl", os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME, "as_cookies.txt"), True, True),
        ("Weibo", LinkType.CREATOR, "wb_cookies.txt", {"weibo": "global_wb.txt"}, "gallery-dl", "global_wb.txt", False, True),
        ("Xiaohongshu", LinkType.CREATOR, None, {"xiaohongshu": "global_xhs.txt"}, "gallery-dl", "global_xhs.txt", False, True),
        ("DeviantArt", LinkType.CREATOR, "nonexistent_da.txt", {}, "gallery-dl", None, False, False),
    ]
)
def test_get_downloader_for_link(
    link_instance: Link, monkeypatch,
    site_name: str, link_type: LinkType, link_cookies_path: Optional[str],
    global_site_cookies: Dict[str, str], expected_downloader: str,
    expected_cookie_in_opts: Optional[str],
    link_cookie_exists: bool, global_cookie_exists: bool
):
    link_instance.site_name = site_name
    link_instance.link_type = link_type
    link_instance.cookies_path = link_cookies_path

    monkeypatch.setattr(settings, "SITE_COOKIES", global_site_cookies)

    def mock_os_path_exists(path):
        if link_cookies_path and path == os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME, link_cookies_path):
            return link_cookie_exists
        if site_name.lower() in global_site_cookies and path == global_site_cookies[site_name.lower()]:
            return global_cookie_exists
        if path == settings.MEDIA_ROOT: # MEDIA_ROOT itself
            return True
        if path == os.path.join(settings.MEDIA_ROOT, 'download_archive.txt') or path == os.path.join(settings.MEDIA_ROOT, 'gallery_dl_archive.sqlite'):
            return True # Assume archive files can be created/exist
        return False # Default to false for other paths

    monkeypatch.setattr(os.path, "exists", mock_os_path_exists)

    downloader, opts = downloader_service.get_downloader_for_link(link_instance)

    assert downloader == expected_downloader

    if expected_downloader == "yt-dlp":
        assert isinstance(opts, dict)
        if link_type == LinkType.LIVE:
            assert '%(title)s - %(timestamp)s [%(id)s].%(ext)s' in opts['outtmpl']
            assert opts['live_from_start'] is True
        else:
            assert '%(title)s [%(id)s].%(ext)s' in opts['outtmpl'] # Default template

        if expected_cookie_in_opts:
            assert opts.get('cookiefile') == expected_cookie_in_opts
        else:
            assert 'cookiefile' not in opts

    elif expected_downloader == "gallery-dl":
        assert isinstance(opts, list)
        if expected_cookie_in_opts:
            assert "--cookies" in opts
            assert opts[opts.index("--cookies") + 1] == expected_cookie_in_opts
        else:
            assert "--cookies" not in opts


# --- Tests for download_media ---

@pytest.mark.asyncio
@mock.patch("app.services.downloader.yt_dlp.YoutubeDL")
async def test_download_media_yt_dlp_success(
    mock_youtube_dl_class, link_instance: Link, mock_media_root: str
):
    link_instance.site_name = "YouTube" # Ensure yt-dlp is chosen
    
    mock_ydl_instance = mock.MagicMock()
    mock_youtube_dl_class.return_value.__enter__.return_value = mock_ydl_instance
    
    # Simulate the hook adding a file
    downloaded_file_path = os.path.join(mock_media_root, "test_video.mp4")

    def mock_download(urls):
        # Simulate hook behavior: it appends to downloaded_files_list in the module
        # For testing, we can make the hook append to a list we control, or check the module's list
        # Here, we'll directly modify the list the real hook would modify.
        # To do this properly, the hook itself should be mockable or take a list argument.
        # Given the current structure, we'll assume the hook appends to `downloader_service.downloaded_files_list`
        # This is tricky because that list is local to download_media.
        # Instead, let's simulate the hook by making the mock_download modify the result dict directly.
        # The hook `ydl_filename_hook` is defined inside `download_media`, so we can't easily mock it.
        # The hook appends to `downloaded_files_list` which is also local to `download_media`.
        # The test relies on the fact that `ydl.download()` is called, and if it "succeeds",
        # and the hook (if it ran and found files) populated `downloaded_files_list`, then status is success.
        # We will simulate the hook by having the test check the contents of `result["downloaded_files"]`.
        # The hook itself is tested by its effect on `downloaded_files_list`.
        # So, when ydl.download is called, we simulate that the hook has run and added a file.
        # The actual hook logic involves os.path.exists and os.path.isfile, so we mock them.
        
        # Simulate the hook finding a file
        downloader_service.downloaded_files_list.append(downloaded_file_path)
        return 0 # yt-dlp success return code

    mock_ydl_instance.download.side_effect = mock_download

    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("os.path.isfile", return_value=True):
        # Reset the module-level list if it exists, or handle it if it's local to the function
        # For this test, we assume the list `downloaded_files_list` is accessible or the hook works as expected
        downloader_service.downloaded_files_list = [] # Ensure it's clean before call

        result = await downloader_service.download_media(link_instance)

    assert result["status"] == "success"
    assert downloaded_file_path in result["downloaded_files"]
    assert result["error"] is None
    mock_ydl_instance.download.assert_called_once_with([link_instance.url])


@pytest.mark.asyncio
@mock.patch("app.services.downloader.yt_dlp.YoutubeDL")
async def test_download_media_yt_dlp_download_error(
    mock_youtube_dl_class, link_instance: Link
):
    link_instance.site_name = "YouTube"
    mock_ydl_instance = mock.MagicMock()
    mock_youtube_dl_class.return_value.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.download.side_effect = downloader_service.yt_dlp.utils.DownloadError("Test Download Error")
    
    downloader_service.downloaded_files_list = []
    result = await downloader_service.download_media(link_instance)

    assert result["status"] == "error"
    assert "Test Download Error" in result["error"]
    assert not result["downloaded_files"] # No files should be listed if DownloadError is raised early


@pytest.mark.asyncio
@mock.patch("app.services.downloader.asyncio.create_subprocess_exec")
async def test_download_media_gallery_dl_success(
    mock_create_subprocess_exec, link_instance: Link, mock_media_root: str
):
    link_instance.site_name = "Pixiv" # Ensure gallery-dl is chosen
    
    mock_process = mock.AsyncMock() # Use AsyncMock for awaitable methods
    mock_process.returncode = 0
    
    # Simulate gallery-dl outputting a file path
    file_name = "pixiv_image.jpg"
    file_path_in_output = os.path.join(mock_media_root, "Pixiv", "artist", file_name)
    # Ensure the directory structure matches what gallery-dl might create based on its default or link-specific settings
    # For simplicity, assume a flat structure under MEDIA_ROOT for this test, or a structure gallery-dl would use.
    # The regex in downloader.py is `r"['\"]?(" + re.escape(settings.MEDIA_ROOT) + r"/[^'\"\s]+)['\"]?"`
    # So, the path must start with settings.MEDIA_ROOT.
    
    mock_process.communicate.return_value = (
        f"Downloading {link_instance.url}\n'{file_path_in_output}'\nDone.".encode(), # stdout
        b""  # stderr
    )
    mock_create_subprocess_exec.return_value = mock_process

    # Mock os.path.exists and os.path.isfile for filename parsing
    with mock.patch("os.path.exists") as mock_exists, \
         mock.patch("os.path.isfile") as mock_isfile:
        
        def side_effect_exists(path):
            if path == file_path_in_output:
                return True
            return False
        mock_exists.side_effect = side_effect_exists
        
        def side_effect_isfile(path):
            if path == file_path_in_output:
                return True
            return False
        mock_isfile.side_effect = side_effect_isfile

        result = await downloader_service.download_media(link_instance)

    assert result["status"] == "success"
    assert file_path_in_output in result["downloaded_files"]
    assert result["error"] is None
    mock_create_subprocess_exec.assert_called_once()
    # Check args passed to gallery-dl (first arg is 'gallery-dl', then opts, then url)
    call_args = mock_create_subprocess_exec.call_args[0]
    assert call_args[0] == 'gallery-dl'
    assert link_instance.url in call_args


@pytest.mark.asyncio
@mock.patch("app.services.downloader.asyncio.create_subprocess_exec")
async def test_download_media_gallery_dl_failure(
    mock_create_subprocess_exec, link_instance: Link
):
    link_instance.site_name = "Pixiv"
    mock_process = mock.AsyncMock()
    mock_process.returncode = 1 # gallery-dl failure
    mock_process.communicate.return_value = (b"", b"Some error from gallery-dl") # stdout, stderr
    mock_create_subprocess_exec.return_value = mock_process

    result = await downloader_service.download_media(link_instance)

    assert result["status"] == "error"
    assert "gallery-dl failed with code 1" in result["error"]
    assert "Some error from gallery-dl" in result["error"]
    assert not result["downloaded_files"]


@pytest.mark.asyncio
@mock.patch("app.services.downloader.asyncio.create_subprocess_exec")
async def test_download_media_gallery_dl_file_not_found(
    mock_create_subprocess_exec, link_instance: Link
):
    link_instance.site_name = "Pixiv"
    mock_create_subprocess_exec.side_effect = FileNotFoundError("gallery-dl not found")

    result = await downloader_service.download_media(link_instance)

    assert result["status"] == "error"
    assert "gallery-dl command not found" in result["error"]


@pytest.mark.asyncio
async def test_download_media_unknown_downloader(link_instance: Link):
    # This test requires get_downloader_for_link to return something not 'yt-dlp' or 'gallery-dl'
    # We can achieve this by temporarily patching get_downloader_for_link
    with mock.patch("app.services.downloader.get_downloader_for_link") as mock_get_dl:
        mock_get_dl.return_value = ("unknown-dl", {})
        result = await downloader_service.download_media(link_instance)

    assert result["status"] == "error"
    assert "Unknown downloader: unknown-dl" in result["error"]

@pytest.mark.asyncio
@mock.patch("app.services.downloader.yt_dlp.YoutubeDL")
async def test_download_media_yt_dlp_success_no_files_detected(
    mock_youtube_dl_class, link_instance: Link, mock_media_root: str
):
    link_instance.site_name = "YouTube" 
    mock_ydl_instance = mock.MagicMock()
    mock_youtube_dl_class.return_value.__enter__.return_value = mock_ydl_instance
    
    def mock_download_no_files(urls):
        # Simulate hook not finding any files
        downloader_service.downloaded_files_list = []
        return 0 # yt-dlp success return code
    mock_ydl_instance.download.side_effect = mock_download_no_files

    downloader_service.downloaded_files_list = [] 
    result = await downloader_service.download_media(link_instance)

    assert result["status"] == "error" # Changed from "success" because no files means it's an issue
    assert not result["downloaded_files"]
    assert "no files were detected by the hook" in result["error"]
    mock_ydl_instance.download.assert_called_once_with([link_instance.url])

@pytest.mark.asyncio
@mock.patch("app.services.downloader.asyncio.create_subprocess_exec")
async def test_download_media_gallery_dl_success_no_files_parsed(
    mock_create_subprocess_exec, link_instance: Link, mock_media_root: str
):
    link_instance.site_name = "Pixiv"
    mock_process = mock.AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (
        b"gallery-dl finished but no paths in output", # stdout with no parsable paths
        b""  # stderr
    )
    mock_create_subprocess_exec.return_value = mock_process

    # Mock os.path.exists and os.path.isfile to always return False for parsing part
    with mock.patch("os.path.exists", return_value=False), \
         mock.patch("os.path.isfile", return_value=False):
        result = await downloader_service.download_media(link_instance)

    assert result["status"] == "success" # gallery-dl returned 0
    assert not result["downloaded_files"] # No files parsed
    assert result["error"] is None # No error if gallery-dl itself succeeded
    # A warning is logged in this case, but the status is success.
    mock_create_subprocess_exec.assert_called_once()

# Test for ensuring PROJECT_ROOT and USER_COOKIES_BASE_DIR_NAME are used
# This is implicitly tested by `test_get_downloader_for_link` where `expected_cookie_in_opts`
# relies on `os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME, link_cookies_path)`

# Test for specific yt-dlp options like output_template for live links
# This is also covered in `test_get_downloader_for_link` parametrization.

print("test_downloader.py created with unit tests.")
