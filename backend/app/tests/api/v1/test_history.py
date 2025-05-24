# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import httpx
from typing import Dict, List, Optional, Any
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.models import Link, LinkType, HistoryLog, HistoryLogCreate, HistoryLogRead
from app.tests.conftest import TestSessionFactory # Import test DB session factory

logger = logging.getLogger(__name__)

# --- Helper Functions ---

async def create_test_link_for_history(client: httpx.AsyncClient, headers: Dict[str, str], url: str, name: str) -> Dict:
    """Creates a test link and returns its dictionary representation."""
    link_data = {
        "url": url,
        "link_type": LinkType.CREATOR, # Assuming LinkType.CREATOR is a valid enum member
        "name": name,
        "description": f"Desc for {name}",
        "tags": f"history_test,{name.lower()}",
    }
    response = await client.post(f"{settings.API_V1_STR}/links/", json=link_data, headers=headers)
    assert response.status_code == 201, f"Failed to create link for history testing: {response.text}"
    return response.json()

async def create_history_log_directly(
    db: AsyncSession,
    link_id: int,
    status: str = "success",
    output: str = "Test output",
    timestamp: Optional[datetime] = None
) -> HistoryLog:
    """Directly creates a history log entry in the database."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    history_log_create = HistoryLogCreate(
        link_id=link_id,
        status=status,
        output=output,
        timestamp=timestamp
    )
    history_log = HistoryLog.model_validate(history_log_create) # Use model_validate for pydantic v2
    db.add(history_log)
    await db.commit()
    await db.refresh(history_log)
    return history_log

# --- Test Cases ---

@pytest.mark.asyncio
async def test_read_history_logs_empty(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """Test reading history logs when none exist (initially)."""
    # Clear existing history logs (and links to be safe, as they might cascade or be related)
    async with TestSessionFactory() as session:
        await session.execute(select(HistoryLog).delete()) # More direct way to delete
        await session.execute(select(Link).delete()) # Clear links to avoid FK issues or leftover data
        await session.commit()

    response = await client.get(f"{settings.API_V1_STR}/history/", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_and_read_history_logs(
    client: httpx.AsyncClient,
    superuser_token_headers: Dict[str, str]
) -> None:
    """Test creating history logs (indirectly via link or directly) and reading them."""
    # 1. Create a Link
    link_dict = await create_test_link_for_history(
        client, superuser_token_headers, "https://example.com/history_test_1", "History Test Link 1"
    )
    link_id_1 = link_dict["id"]

    link_dict_2 = await create_test_link_for_history(
        client, superuser_token_headers, "https://example.com/history_test_2", "History Test Link 2"
    )
    link_id_2 = link_dict_2["id"]

    # 2. Create HistoryLog entries directly for these links
    async with TestSessionFactory() as session:
        log1 = await create_history_log_directly(session, link_id_1, status="success", output="Log 1 for link 1")
        log2 = await create_history_log_directly(session, link_id_1, status="failed", output="Log 2 for link 1")
        log3 = await create_history_log_directly(session, link_id_2, status="success", output="Log 1 for link 2")

    # 3. Read all history logs
    response = await client.get(f"{settings.API_V1_STR}/history/", headers=superuser_token_headers)
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 3
    log_outputs = [log["output"] for log in logs]
    assert "Log 1 for link 1" in log_outputs
    assert "Log 2 for link 1" in log_outputs
    assert "Log 1 for link 2" in log_outputs

    # 4. Test filtering by link_id
    response_link1 = await client.get(f"{settings.API_V1_STR}/history/?link_id={link_id_1}", headers=superuser_token_headers)
    assert response_link1.status_code == 200
    logs_link1 = response_link1.json()
    assert len(logs_link1) == 2
    for log in logs_link1:
        assert log["link_id"] == link_id_1

    # 5. Test filtering by status
    response_success = await client.get(f"{settings.API_V1_STR}/history/?status=success", headers=superuser_token_headers)
    assert response_success.status_code == 200
    logs_success = response_success.json()
    assert len(logs_success) == 2 # log1 and log3
    for log in logs_success:
        assert log["status"] == "success"
        
    response_failed = await client.get(f"{settings.API_V1_STR}/history/?status=failed", headers=superuser_token_headers)
    assert response_failed.status_code == 200
    logs_failed = response_failed.json()
    assert len(logs_failed) == 1 # log2
    assert logs_failed[0]["status"] == "failed"

    # 6. Test filtering by link_id and status
    response_link1_success = await client.get(f"{settings.API_V1_STR}/history/?link_id={link_id_1}&status=success", headers=superuser_token_headers)
    assert response_link1_success.status_code == 200
    logs_link1_success = response_link1_success.json()
    assert len(logs_link1_success) == 1
    assert logs_link1_success[0]["link_id"] == link_id_1
    assert logs_link1_success[0]["status"] == "success"
    assert logs_link1_success[0]["output"] == "Log 1 for link 1"

    # 7. Test pagination (skip and limit)
    response_limit1 = await client.get(f"{settings.API_V1_STR}/history/?limit=1", headers=superuser_token_headers)
    assert response_limit1.status_code == 200
    logs_limit1 = response_limit1.json()
    assert len(logs_limit1) == 1
    # Logs are ordered by timestamp desc by default in the API
    assert logs_limit1[0]["id"] == log3.id # log3 was the last created

    response_skip1_limit1 = await client.get(f"{settings.API_V1_STR}/history/?skip=1&limit=1", headers=superuser_token_headers)
    assert response_skip1_limit1.status_code == 200
    logs_skip1_limit1 = response_skip1_limit1.json()
    assert len(logs_skip1_limit1) == 1
    assert logs_skip1_limit1[0]["id"] == log2.id # log2 was the second to last

@pytest.mark.asyncio
async def test_read_history_logs_unauthorized(client: httpx.AsyncClient) -> None:
    """Test reading history logs without authentication."""
    response = await client.get(f"{settings.API_V1_STR}/history/")
    assert response.status_code == 401 # Expecting 401 Unauthorized

@pytest.mark.asyncio
async def test_delete_history_log(
    client: httpx.AsyncClient,
    superuser_token_headers: Dict[str, str]
) -> None:
    """Test deleting a specific history log."""
    # 1. Create a Link and a HistoryLog
    link_dict = await create_test_link_for_history(
        client, superuser_token_headers, "https://example.com/history_delete_test", "History Delete Test Link"
    )
    link_id = link_dict["id"]
    async with TestSessionFactory() as session:
        history_log = await create_history_log_directly(session, link_id, output="Log to be deleted")
    
    history_log_id = history_log.id

    # 2. Delete the history log
    delete_response = await client.delete(f"{settings.API_V1_STR}/history/{history_log_id}", headers=superuser_token_headers)
    assert delete_response.status_code == 200
    deleted_log_data = delete_response.json()
    assert deleted_log_data["id"] == history_log_id
    assert deleted_log_data["output"] == "Log to be deleted"

    # 3. Verify it's deleted (by trying to fetch it via API - though not directly possible with current GET endpoint)
    # Instead, verify it's not in the list of all logs for that link
    response = await client.get(f"{settings.API_V1_STR}/history/?link_id={link_id}", headers=superuser_token_headers)
    assert response.status_code == 200
    logs_for_link = response.json()
    for log in logs_for_link:
        assert log["id"] != history_log_id
    
    # Also verify with direct DB check
    async with TestSessionFactory() as session:
        deleted_log_db = await session.get(HistoryLog, history_log_id)
        assert deleted_log_db is None


@pytest.mark.asyncio
async def test_delete_history_log_not_found(
    client: httpx.AsyncClient,
    superuser_token_headers: Dict[str, str]
) -> None:
    """Test deleting a history log that does not exist."""
    non_existent_id = 999999
    delete_response = await client.delete(f"{settings.API_V1_STR}/history/{non_existent_id}", headers=superuser_token_headers)
    assert delete_response.status_code == 404
    assert "not found" in delete_response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_delete_history_log_unauthorized(client: httpx.AsyncClient) -> None:
    """Test deleting a history log without authentication."""
    # We don't need to create a log, just attempt to delete any ID
    response = await client.delete(f"{settings.API_V1_STR}/history/123") # 123 is a placeholder ID
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_delete_history_logs_by_link(
    client: httpx.AsyncClient,
    superuser_token_headers: Dict[str, str]
) -> None:
    """Test deleting all history logs for a specific link."""
    # 1. Create two Links
    link1_dict = await create_test_link_for_history(
        client, superuser_token_headers, "https://example.com/history_by_link_1", "History By Link 1"
    )
    link1_id = link1_dict["id"]
    link2_dict = await create_test_link_for_history(
        client, superuser_token_headers, "https://example.com/history_by_link_2", "History By Link 2"
    )
    link2_id = link2_dict["id"]

    # 2. Create HistoryLog entries for both links
    async with TestSessionFactory() as session:
        await create_history_log_directly(session, link1_id, output="Log 1 for link 1 (by_link test)")
        await create_history_log_directly(session, link1_id, output="Log 2 for link 1 (by_link test)")
        await create_history_log_directly(session, link2_id, output="Log 1 for link 2 (by_link test)")

    # 3. Delete history logs for link1_id
    delete_response = await client.delete(f"{settings.API_V1_STR}/history/by_link/{link1_id}", headers=superuser_token_headers)
    assert delete_response.status_code == 200
    response_data = delete_response.json()
    assert response_data["message"] == f"Successfully deleted 2 history logs for link_id {link1_id}"

    # 4. Verify logs for link1_id are deleted
    response_link1 = await client.get(f"{settings.API_V1_STR}/history/?link_id={link1_id}", headers=superuser_token_headers)
    assert response_link1.status_code == 200
    assert response_link1.json() == []

    # 5. Verify logs for link2_id still exist
    response_link2 = await client.get(f"{settings.API_V1_STR}/history/?link_id={link2_id}", headers=superuser_token_headers)
    assert response_link2.status_code == 200
    logs_link2 = response_link2.json()
    assert len(logs_link2) == 1
    assert logs_link2[0]["output"] == "Log 1 for link 2 (by_link test)"

@pytest.mark.asyncio
async def test_delete_history_logs_by_link_link_not_found(
    client: httpx.AsyncClient,
    superuser_token_headers: Dict[str, str]
) -> None:
    """Test deleting history logs for a non-existent link_id."""
    non_existent_link_id = 888888
    delete_response = await client.delete(
        f"{settings.API_V1_STR}/history/by_link/{non_existent_link_id}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 404 # As per API endpoint, it checks if link exists
    assert f"Link with id {non_existent_link_id} not found" in delete_response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_history_logs_by_link_no_history(
    client: httpx.AsyncClient,
    superuser_token_headers: Dict[str, str]
) -> None:
    """Test deleting history logs for a link that has no history."""
    # 1. Create a Link
    link_dict = await create_test_link_for_history(
        client, superuser_token_headers, "https://example.com/history_no_logs", "No History Link"
    )
    link_id = link_dict["id"]

    # 2. Attempt to delete history logs for this link (which has none)
    delete_response = await client.delete(f"{settings.API_V1_STR}/history/by_link/{link_id}", headers=superuser_token_headers)
    assert delete_response.status_code == 200
    response_data = delete_response.json()
    assert response_data["message"] == f"Successfully deleted 0 history logs for link_id {link_id}"

    # 3. Verify no logs are present (should still be empty)
    response_link = await client.get(f"{settings.API_V1_STR}/history/?link_id={link_id}", headers=superuser_token_headers)
    assert response_link.status_code == 200
    assert response_link.json() == []


@pytest.mark.asyncio
async def test_delete_history_logs_by_link_unauthorized(client: httpx.AsyncClient) -> None:
    """Test deleting history logs by link_id without authentication."""
    response = await client.delete(f"{settings.API_V1_STR}/history/by_link/123") # 123 is a placeholder link_id
    assert response.status_code == 401

# Note: The GET /history/{history_id} endpoint is not present in the provided history.py.
# If it were, tests for it would be structured similarly to test_read_link in test_links.py:
# async def test_read_single_history_log(client, superuser_token_headers): ...
# async def test_read_single_history_log_not_found(client, superuser_token_headers): ...
# async def test_read_single_history_log_unauthorized(client): ...

# Ensure all async functions `await` calls to client and TestSessionFactory
# Ensure proper headers are passed for authenticated endpoints.
# Ensure correct status codes and response bodies are asserted.
# Clean up created data if necessary, though TestSessionFactory usually handles rollbacks for test isolation.
# A test to clear all links and history logs at the beginning of the module or session might be useful
# if tests are not perfectly isolated and data leakage is a concern.
# For now, individual tests try to manage their data or test against empty states.
print("test_history.py created with initial tests.")
