# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link, LinkCreate, LinkType
from app.models.history import HistoryLog, HistoryLogCreate, HistoryStatus
from app.crud.crud_history import history_log as crud_history_log
from app.crud.crud_link import link as crud_link # To create prerequisite Link objects
from app.tests.conftest import TestSessionFactory # For DB interaction

# --- Helper Fixture for Creating Links ---

@pytest.fixture
async def create_test_link(db: AsyncSession) -> Link:
    """Helper fixture to create a test Link in the database."""
    link_in = LinkCreate(
        url="http://testlink.com/path",
        name="Test Link for History",
        link_type=LinkType.CREATOR,
        site_name="TestSite"
    )
    # Use the actual crud_link.create method to ensure consistency
    # For CRUDLink, cookies_path validation might run, so ensure it's None or valid.
    # The LinkCreate model does not have cookies_path, so it should be fine.
    created_link = await crud_link.create(db=db, obj_in=link_in)
    return created_link

# --- Tests for CRUDHistoryLog specific methods ---

@pytest.mark.asyncio
async def test_create_log_all_fields(db: AsyncSession, create_test_link: Link):
    """Test creating a history log with all fields provided."""
    log_data = {
        "link_id": create_test_link.id,
        "status": HistoryStatus.SUCCESS,
        "downloaded_files": ["file1.mp4", "file2.jpg"],
        "error_message": None,
        "details": {"size": "10MB", "duration": "5min"}
    }
    created_log = await crud_history_log.create_log(db=db, **log_data)

    assert created_log.id is not None
    assert created_log.link_id == log_data["link_id"]
    assert created_log.status == log_data["status"]
    assert created_log.downloaded_files == log_data["downloaded_files"]
    assert created_log.error_message == log_data["error_message"]
    assert created_log.details == log_data["details"]
    assert isinstance(created_log.timestamp, datetime)
    assert (datetime.now(timezone.utc) - created_log.timestamp).total_seconds() < 5 # Check if timestamp is recent

@pytest.mark.asyncio
async def test_create_log_optional_fields_omitted(db: AsyncSession, create_test_link: Link):
    """Test creating a history log with optional fields omitted."""
    log_data = {
        "link_id": create_test_link.id,
        "status": HistoryStatus.FAILURE,
        "error_message": "A critical error occurred."
        # downloaded_files and details are omitted
    }
    created_log = await crud_history_log.create_log(db=db, **log_data)

    assert created_log.id is not None
    assert created_log.link_id == log_data["link_id"]
    assert created_log.status == log_data["status"]
    assert created_log.error_message == log_data["error_message"]
    assert created_log.downloaded_files is None # Should default to None or empty list based on model
    assert created_log.details is None
    assert isinstance(created_log.timestamp, datetime)

@pytest.mark.asyncio
async def test_get_multi_by_link(db: AsyncSession, create_test_link: Link):
    """Test fetching multiple history logs for a specific link, with pagination and ordering."""
    link1_id = create_test_link.id
    
    # Create another link for isolation
    other_link_in = LinkCreate(url="http://otherlink.com", name="Other Link", link_type=LinkType.OTHER)
    other_link = await crud_link.create(db=db, obj_in=other_link_in)
    other_link_id = other_link.id

    # Create history logs for link1
    log1_l1 = await crud_history_log.create_log(db=db, link_id=link1_id, status=HistoryStatus.SUCCESS, details={"order": 1})
    await asyncio.sleep(0.01) # Ensure timestamp difference
    log2_l1 = await crud_history_log.create_log(db=db, link_id=link1_id, status=HistoryStatus.FAILURE, error_message="err1", details={"order": 2})
    await asyncio.sleep(0.01)
    log3_l1 = await crud_history_log.create_log(db=db, link_id=link1_id, status=HistoryStatus.SUCCESS, downloaded_files=["f1"], details={"order": 3})

    # Create history log for other_link
    await crud_history_log.create_log(db=db, link_id=other_link_id, status=HistoryStatus.SUCCESS)

    # Test fetching all logs for link1
    logs_l1_all = await crud_history_log.get_multi_by_link(db=db, link_id=link1_id, limit=10)
    assert len(logs_l1_all) == 3
    assert [log.details["order"] for log in logs_l1_all] == [3, 2, 1] # Ordered by timestamp desc

    # Test pagination: skip 1, limit 1
    logs_l1_paginated = await crud_history_log.get_multi_by_link(db=db, link_id=link1_id, skip=1, limit=1)
    assert len(logs_l1_paginated) == 1
    assert logs_l1_paginated[0].id == log2_l1.id

    # Test fetching logs for a link with no history
    no_history_link_in = LinkCreate(url="http://nohistory.com", name="No History Link", link_type=LinkType.OTHER)
    no_history_link = await crud_link.create(db=db, obj_in=no_history_link_in)
    logs_no_history = await crud_history_log.get_multi_by_link(db=db, link_id=no_history_link.id)
    assert len(logs_no_history) == 0

@pytest.mark.asyncio
async def test_remove_by_link(db: AsyncSession, create_test_link: Link):
    """Test removing history logs by link_id."""
    link1_id = create_test_link.id
    other_link_in = LinkCreate(url="http://otherlinkremove.com", name="Other Link Remove", link_type=LinkType.OTHER)
    other_link = await crud_link.create(db=db, obj_in=other_link_in)
    other_link_id = other_link.id

    # Create logs for link1
    await crud_history_log.create_log(db=db, link_id=link1_id, status=HistoryStatus.SUCCESS)
    await crud_history_log.create_log(db=db, link_id=link1_id, status=HistoryStatus.SUCCESS)
    
    # Create log for other_link
    log_other_link = await crud_history_log.create_log(db=db, link_id=other_link_id, status=HistoryStatus.SUCCESS)

    # Remove logs for link1
    deleted_count = await crud_history_log.remove_by_link(db=db, link_id=link1_id)
    assert deleted_count == 2

    # Verify logs for link1 are deleted
    logs_l1_after_delete = await crud_history_log.get_multi_by_link(db=db, link_id=link1_id)
    assert len(logs_l1_after_delete) == 0

    # Verify logs for other_link are not affected
    logs_other_link_after_delete = await crud_history_log.get_multi_by_link(db=db, link_id=other_link_id)
    assert len(logs_other_link_after_delete) == 1
    assert logs_other_link_after_delete[0].id == log_other_link.id

    # Test removing logs for a link with no history
    no_history_link_in = LinkCreate(url="http://nohistoryremove.com", name="No History Link Remove", link_type=LinkType.OTHER)
    no_history_link = await crud_link.create(db=db, obj_in=no_history_link_in)
    deleted_count_no_history = await crud_history_log.remove_by_link(db=db, link_id=no_history_link.id)
    assert deleted_count_no_history == 0

# --- Tests for CRUDBase generic methods using HistoryLog model ---

@pytest.mark.asyncio
async def test_crudbase_get(db: AsyncSession, create_test_link: Link):
    """Test CRUDBase.get() method with HistoryLog."""
    log_created = await crud_history_log.create_log(db=db, link_id=create_test_link.id, status=HistoryStatus.SUCCESS)
    log_fetched = await crud_history_log.get(db=db, id=log_created.id)
    
    assert log_fetched is not None
    assert log_fetched.id == log_created.id
    assert log_fetched.status == HistoryStatus.SUCCESS

    non_existent_log = await crud_history_log.get(db=db, id=99999)
    assert non_existent_log is None

@pytest.mark.asyncio
async def test_crudbase_get_multi(db: AsyncSession, create_test_link: Link):
    """Test CRUDBase.get_multi() method with HistoryLog."""
    log1 = await crud_history_log.create_log(db=db, link_id=create_test_link.id, status=HistoryStatus.SUCCESS, details={"order": 1})
    await asyncio.sleep(0.01) # ensure timestamp difference for ordering if default order is applied
    log2 = await crud_history_log.create_log(db=db, link_id=create_test_link.id, status=HistoryStatus.FAILURE, details={"order": 2})
    
    # Test get_multi without specific ordering (relies on insertion order or PK if no default in model)
    all_logs = await crud_history_log.get_multi(db=db, limit=10)
    assert len(all_logs) >= 2 # Could be more if other tests ran without full isolation
    
    # Check if our logs are present
    log_ids = [log.id for log in all_logs]
    assert log1.id in log_ids
    assert log2.id in log_ids

    # Test with pagination
    paginated_logs = await crud_history_log.get_multi(db=db, skip=0, limit=1, order_by=[HistoryLog.timestamp.asc()])
    assert len(paginated_logs) == 1
    # To make this assertion robust, we need to ensure log1 is indeed the first by timestamp.
    # If default order_by is not timestamp, this might be tricky. Let's assume for now it's ordered by ID or insertion.
    # For HistoryLog, get_multi_by_link orders by timestamp. CRUDBase.get_multi has an order_by param.
    
    # Test with explicit ordering (ascending by timestamp)
    ordered_logs_asc = await crud_history_log.get_multi(db=db, order_by=[HistoryLog.timestamp.asc()], limit=2)
    if len(ordered_logs_asc) == 2 and ordered_logs_asc[0].id == log1.id and ordered_logs_asc[1].id == log2.id:
        # This order is correct if log1 was created before log2
        pass
    elif len(ordered_logs_asc) == 2 and ordered_logs_asc[0].id == log2.id and ordered_logs_asc[1].id == log1.id:
        # This means log2 was created before log1, which is opposite to the code
        pytest.fail("Log creation order seems to be problematic for timestamp ordering test.")
    elif len(ordered_logs_asc) < 2:
        pytest.fail("Not enough logs found for ordering test.")
    
    assert ordered_logs_asc[0].details["order"] == 1
    assert ordered_logs_asc[1].details["order"] == 2


@pytest.mark.asyncio
async def test_crudbase_create(db: AsyncSession, create_test_link: Link):
    """Test CRUDBase.create() method (which create_log uses)."""
    # This is implicitly tested by test_create_log_all_fields and test_create_log_optional_fields_omitted,
    # as crud_history_log.create_log calls self.create().
    # We can add a direct call for completeness if needed, using HistoryLogCreate.
    history_log_in = HistoryLogCreate(
        link_id=create_test_link.id,
        status=HistoryStatus.SUCCESS,
        downloaded_files=["test.file"],
        details={"source": "crudbase_create_test"}
    )
    created_log = await crud_history_log.create(db=db, obj_in=history_log_in)
    
    assert created_log.id is not None
    assert created_log.link_id == history_log_in.link_id
    assert created_log.status == history_log_in.status
    assert created_log.downloaded_files == history_log_in.downloaded_files
    assert created_log.details == history_log_in.details
    assert isinstance(created_log.timestamp, datetime)

@pytest.mark.asyncio
async def test_crudbase_update(db: AsyncSession, create_test_link: Link):
    """Test CRUDBase.update() method with HistoryLog."""
    log_created = await crud_history_log.create_log(
        db=db, link_id=create_test_link.id, status=HistoryStatus.SUCCESS, details={"original_detail": "value1"}
    )
    
    original_timestamp = log_created.timestamp
    await asyncio.sleep(0.01) # Ensure updated_at will be different if CRUDBase.update handles it

    update_data = {
        "status": HistoryStatus.FAILURE,
        "error_message": "Updated error message",
        "details": {"original_detail": "value1", "new_detail": "value2"} # Completely replaces details
    }
    # Note: CRUDHistoryLog uses BaseModel as UpdateSchemaType, so we pass a dict.
    # If a specific HistoryLogUpdate schema existed, we'd use that.
    log_updated = await crud_history_log.update(db=db, db_obj=log_created, obj_in=update_data)

    assert log_updated.id == log_created.id
    assert log_updated.status == update_data["status"]
    assert log_updated.error_message == update_data["error_message"]
    assert log_updated.details == update_data["details"]
    
    # Verify timestamp and updated_at (if HistoryLog model has updated_at)
    # HistoryLog model does not have an explicit `updated_at` field.
    # CRUDBase.update sets `updated_at` if the model has it.
    # So, for HistoryLog, `timestamp` should remain unchanged by this update.
    assert log_updated.timestamp == original_timestamp 
    # If HistoryLog had an `updated_at` field, we would check:
    # assert log_updated.updated_at > original_timestamp (or if it was None before)

@pytest.mark.asyncio
async def test_crudbase_remove(db: AsyncSession, create_test_link: Link):
    """Test CRUDBase.remove() method with HistoryLog."""
    log_created = await crud_history_log.create_log(db=db, link_id=create_test_link.id, status=HistoryStatus.SUCCESS)
    
    log_removed = await crud_history_log.remove(db=db, id=log_created.id)
    assert log_removed is not None
    assert log_removed.id == log_created.id

    log_after_remove = await crud_history_log.get(db=db, id=log_created.id)
    assert log_after_remove is None

    non_existent_removed = await crud_history_log.remove(db=db, id=99999)
    assert non_existent_removed is None

# Note on CRUDBase methods not explicitly tested here:
# - The `CRUDBase.update` method's behavior with a Pydantic schema as `obj_in` (as opposed to a dict)
#   is not directly tested for HistoryLog because `CRUDHistoryLog` defines `UpdateSchemaType` as `BaseModel` (placeholder).
#   If a `HistoryLogUpdate(BaseModel)` schema were defined and used, that path could be tested.
#   However, the current usage with a dict covers the core update logic.

print("test_crud_history.py created with CRUD tests for HistoryLog.")
