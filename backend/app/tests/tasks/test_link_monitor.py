# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import asyncio
from unittest import mock
from typing import List, Optional, Dict, Any

from app.models.link import Link, LinkStatus, LinkType
from app.models.history import HistoryStatus
from app.tasks import link_monitor # The module to test
from app.core.config import settings

@pytest.fixture
def mock_link_instance_creator():
    """Factory fixture to create mock Link instances."""
    def _create_mock_link(
        id: int,
        is_enabled: bool = True,
        status: LinkStatus = LinkStatus.IDLE,
        link_type: LinkType = LinkType.CREATOR,
        url: str = "http://example.com/creator"
    ) -> mock.Mock: # Use mock.Mock for easier attribute setting
        mock_link = mock.Mock(spec=Link)
        mock_link.id = id
        mock_link.is_enabled = is_enabled
        mock_link.status = status
        mock_link.link_type = link_type
        mock_link.url = url
        # Add other attributes if they are accessed in the functions
        return mock_link
    return _create_mock_link


# --- Tests for process_link ---

@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_not_found_or_disabled(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status,
    mock_download_media,
    mock_crud_history_create_log,
    mock_link_instance_creator
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    # Scenario 1: Link not found
    mock_crud_link_get.return_value = None
    await link_monitor.process_link(link_id=1)
    mock_crud_link_update_status.assert_not_called()
    mock_download_media.assert_not_called()
    mock_crud_history_create_log.assert_not_called()

    # Scenario 2: Link disabled
    mock_crud_link_get.reset_mock() # Reset call counts for next scenario
    disabled_link = mock_link_instance_creator(id=2, is_enabled=False)
    mock_crud_link_get.return_value = disabled_link
    await link_monitor.process_link(link_id=2)
    mock_crud_link_update_status.assert_not_called()
    mock_download_media.assert_not_called()
    mock_crud_history_create_log.assert_not_called()


@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_successful_download_creator(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status,
    mock_download_media,
    mock_crud_history_create_log,
    mock_link_instance_creator
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    link_id = 1
    mock_link = mock_link_instance_creator(id=link_id, link_type=LinkType.CREATOR)
    mock_crud_link_get.return_value = mock_link

    download_files = ["file1.mp4"]
    mock_download_media.return_value = {"status": "success", "downloaded_files": download_files}

    await link_monitor.process_link(link_id)

    # Check calls
    mock_crud_link_get.assert_called_once_with(db=mock_db_session, id=link_id)
    
    # update_status calls:
    # 1. To DOWNLOADING
    # 2. To IDLE
    assert mock_crud_link_update_status.call_count == 2
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.DOWNLOADING, is_success=False)
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.IDLE, is_success=True)
    
    mock_download_media.assert_called_once_with(mock_link)
    mock_crud_history_create_log.assert_called_once_with(
        db=mock_db_session,
        link_id=link_id,
        status=HistoryStatus.SUCCESS,
        downloaded_files=download_files
    )

@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_successful_download_live(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status,
    mock_download_media,
    mock_crud_history_create_log,
    mock_link_instance_creator
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    link_id = 1
    mock_link = mock_link_instance_creator(id=link_id, link_type=LinkType.LIVE)
    mock_crud_link_get.return_value = mock_link

    download_files = ["live_recording.ts"]
    mock_download_media.return_value = {"status": "success", "downloaded_files": download_files}

    await link_monitor.process_link(link_id)
    
    assert mock_crud_link_update_status.call_count == 2
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.RECORDING, is_success=False)
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.IDLE, is_success=True)
    
    mock_crud_history_create_log.assert_called_once_with(
        db=mock_db_session,
        link_id=link_id,
        status=HistoryStatus.SUCCESS,
        downloaded_files=download_files
    )


@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_failed_download(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status,
    mock_download_media,
    mock_crud_history_create_log,
    mock_link_instance_creator
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    link_id = 1
    error_message = "Download timed out"
    mock_link = mock_link_instance_creator(id=link_id, link_type=LinkType.CREATOR)
    mock_crud_link_get.return_value = mock_link
    mock_download_media.return_value = {"status": "error", "error": error_message}

    await link_monitor.process_link(link_id)

    assert mock_crud_link_update_status.call_count == 2
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.DOWNLOADING, is_success=False)
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.ERROR, error_message=error_message)
    
    mock_crud_history_create_log.assert_called_once_with(
        db=mock_db_session,
        link_id=link_id,
        status=HistoryStatus.FAILURE,
        error_message=error_message
    )

@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_exception_in_download_media(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status,
    mock_download_media,
    mock_crud_history_create_log,
    mock_link_instance_creator
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    link_id = 1
    exception_message = "Network Error"
    mock_link = mock_link_instance_creator(id=link_id, link_type=LinkType.CREATOR)
    mock_crud_link_get.return_value = mock_link
    mock_download_media.side_effect = Exception(exception_message)

    await link_monitor.process_link(link_id)
    
    # update_status calls:
    # 1. To DOWNLOADING
    # 2. To ERROR (in the except block)
    assert mock_crud_link_update_status.call_count == 2
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.DOWNLOADING, is_success=False)
    # The error message in the except block will be "Processing Exception: Network Error"
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.ERROR, error_message=f"Processing Exception: {exception_message}")
    
    mock_crud_history_create_log.assert_called_once_with(
        db=mock_db_session,
        link_id=link_id,
        status=HistoryStatus.FAILURE,
        error_message=f"Processing Exception: {exception_message}"
    )

@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_exception_initial_crud_get(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status, # This will be called in the outer except block
    mock_download_media,
    mock_crud_history_create_log, # This will be called in the outer except block
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    link_id = 1
    exception_message = "DB connection error on get"
    mock_crud_link_get.side_effect = Exception(exception_message)

    # The process_link function has a try-except around crud.link.get for status update
    # but the main get is outside that inner try-except.
    # Let's trace the code: if initial crud.link.get fails, it goes to the outer except.
    # Inside that, it tries crud.link.get again. Let's make that second one also fail.
    
    # First call to crud.link.get raises, second call (in except block) also raises
    mock_crud_link_get.side_effect = [Exception(exception_message), Exception("Second DB error")]

    await link_monitor.process_link(link_id)

    # crud.link.get called twice (once in main try, once in except block)
    assert mock_crud_link_get.call_count == 2
    
    # update_status should NOT be called because the link object couldn't be retrieved even in the except block.
    # However, the code tries to update status using `link_for_status` which would be None.
    # The `crud.link.update_status` in the except block will be called with `link_for_status=None` (if get fails again)
    # or if the second get succeeded, it would be called.
    # The current code: `if link_for_status: await crud.link.update_status(...)`
    # So if the second get fails, update_status is NOT called.
    mock_crud_link_update_status.assert_not_called()
    mock_download_media.assert_not_called()
    # History log also depends on link_for_status being found on the second attempt.
    mock_crud_history_create_log.assert_not_called()


@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.crud.history_log.create_log", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.download_media", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.update_status", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.crud.link.get", new_callable=mock.AsyncMock)
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_process_link_exception_initial_update_status(
    mock_async_session_factory,
    mock_crud_link_get,
    mock_crud_link_update_status,
    mock_download_media,
    mock_crud_history_create_log,
    mock_link_instance_creator
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    link_id = 1
    exception_message = "DB connection error on update_status"
    mock_link = mock_link_instance_creator(id=link_id)
    mock_crud_link_get.return_value = mock_link
    
    # First call to update_status (e.g. to DOWNLOADING) raises an exception
    mock_crud_link_update_status.side_effect = [Exception(exception_message), None] # Second call (in except) is fine

    await link_monitor.process_link(link_id)

    # crud.link.get called twice (once in main try, once in except block to get link_for_status)
    assert mock_crud_link_get.call_count == 2
    
    # crud.link.update_status called twice:
    # 1. The one that fails (e.g., setting to DOWNLOADING)
    # 2. The one in the except block (setting to ERROR)
    assert mock_crud_link_update_status.call_count == 2
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.DOWNLOADING, is_success=False)
    mock_crud_link_update_status.assert_any_call(db=mock_db_session, db_obj=mock_link, status=LinkStatus.ERROR, error_message=f"Processing Exception: {exception_message}")
    
    mock_download_media.assert_not_called() # Should not be reached if initial update_status fails

    # History log should be created for the failure
    mock_crud_history_create_log.assert_called_once_with(
        db=mock_db_session,
        link_id=link_id,
        status=HistoryStatus.FAILURE,
        error_message=f"Processing Exception: {exception_message}"
    )


# --- Tests for trigger_monitoring_job ---

@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.process_link", new_callable=mock.AsyncMock) # Mock the actual processing
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_trigger_monitoring_job_no_enabled_links(
    mock_async_session_factory,
    mock_process_link_task # Patched process_link
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session
    
    # Simulate db.execute(...).scalars().all() returning an empty list
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

    with mock.patch.object(link_monitor.logger, "info") as mock_logger_info:
        await link_monitor.trigger_monitoring_job()

    mock_db_session.execute.assert_called_once() # Check that a select query was made
    mock_process_link_task.assert_not_called()
    
    # Check logger calls
    mock_logger_info.assert_any_call("Scheduler triggered: Starting monitoring job for all enabled links...")
    mock_logger_info.assert_any_call("Scheduler job: No enabled and idle links found to process.")


@pytest.mark.asyncio
@mock.patch("app.tasks.link_monitor.asyncio.gather", new_callable=mock.AsyncMock) # Mock gather to avoid waiting
@mock.patch("app.tasks.link_monitor.asyncio.create_task") # Mock create_task
@mock.patch("app.tasks.link_monitor.process_link", new_callable=mock.AsyncMock) # Mock the actual processing
@mock.patch("app.tasks.link_monitor.AsyncSessionFactory")
async def test_trigger_monitoring_job_multiple_links(
    mock_async_session_factory,
    mock_process_link_func, # This is the mocked app.tasks.link_monitor.process_link
    mock_create_task,
    mock_asyncio_gather,
    mock_link_instance_creator,
    monkeypatch
):
    mock_db_session = mock.AsyncMock()
    mock_async_session_factory.return_value.__aenter__.return_value = mock_db_session

    # Create some mock links
    link1 = mock_link_instance_creator(id=1, url="url1")
    link2 = mock_link_instance_creator(id=2, url="url2", status=LinkStatus.IDLE)
    # Link3 is enabled but in a state that should be skipped by the query
    link3 = mock_link_instance_creator(id=3, url="url3", status=LinkStatus.DOWNLOADING)

    # The query in trigger_monitoring_job filters for is_enabled=True and status not in DOWNLOADING, RECORDING, MONITORING
    # So, link1 and link2 should be processed if they are "enabled" and "idle".
    # The mock_link_instance_creator defaults to is_enabled=True, status=IDLE.
    
    enabled_links_from_db = [link1, link2] # link3 should be filtered out by the SQL query logic
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = enabled_links_from_db
    
    # Mock create_task to just return a dummy task object (or a mock that can be awaited)
    # The important part is that process_link_with_semaphore is called within create_task
    dummy_task = mock.AsyncMock() 
    mock_create_task.return_value = dummy_task

    monkeypatch.setattr(settings, "MAX_CONCURRENT_DOWNLOADS", 1) # Test semaphore implicitly

    with mock.patch.object(link_monitor.logger, "info") as mock_logger_info:
        await link_monitor.trigger_monitoring_job()

    mock_db_session.execute.assert_called_once()
    assert mock_create_task.call_count == len(enabled_links_from_db)
    
    # Check that process_link_with_semaphore (which calls the mocked process_link_func) was scheduled
    # We are not directly checking calls to process_link_func because it's wrapped.
    # Instead, we check that create_task was called for each eligible link.
    # The actual execution of process_link_func would be tested by the semaphore logic if not mocked out.
    # Here, we verify that tasks were created for link1 and link2.
    
    # To verify that the correct link_ids were passed to create_task's argument (the coroutine):
    # We can inspect the calls to `create_task`. The first argument to `create_task` is the coroutine.
    # This coroutine is `process_link_with_semaphore(link.id, semaphore)`.
    # It's a bit complex to assert the arguments of the coroutine directly from `mock_create_task.call_args_list`.
    # A simpler check is that create_task was called the right number of times.
    # And that the logger messages show the correct link IDs.

    mock_logger_info.assert_any_call(f"Scheduler job: Created task for link_id: {link1.id} ({link1.url})")
    mock_logger_info.assert_any_call(f"Scheduler job: Created task for link_id: {link2.id} ({link2.url})")
    
    # Check if asyncio.gather was called with the created tasks
    mock_asyncio_gather.assert_called_once_with(*[dummy_task for _ in enabled_links_from_db])
    
    mock_logger_info.assert_any_call(f"Scheduler job: Finished processing {len(enabled_links_from_db)} links.")

print("test_link_monitor.py created with unit tests.")
