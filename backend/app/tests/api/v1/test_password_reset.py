# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core import security
from app.models import User, UserCreate, PasswordResetToken # Assuming PasswordResetToken is in app.models
from app.crud import user as crud_user
from app.crud import password_reset_token as crud_password_reset_token # Assuming this exists
from app.tests.conftest import TestSessionFactory # Import test DB session factory
from app.api.v1.endpoints.password_reset import GenerateResetTokenResponse # Response model

# Helper to create a user directly in DB
async def create_test_user_for_password_reset(db: AsyncSession, username: str, email: str, password: str) -> User:
    user_in = UserCreate(username=username, email=email, password=password)
    # Use the synchronous create_user_sync or adapt if an async version is available in crud_user
    # For this example, let's assume crud_user.create can handle it or we use a direct model approach
    # db_user = await crud_user.create(db=db, obj_in=user_in) # If crud_user.create is async and suitable

    # Simplified user creation for test setup if crud_user.create is complex or sync-only
    hashed_password = security.get_password_hash(password)
    db_user = User(username=username, email=email, hashed_password=hashed_password, is_active=True, is_superuser=False)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- Test Cases for POST /password-recovery/{username} ---

@pytest.mark.asyncio
async def test_recover_password_generate_token_success(
    client: httpx.AsyncClient,
    # superuser_token_headers: Dict[str, str] # Not needed for this public endpoint
) -> None:
    """Test successful generation of a password reset token."""
    test_username = "testrecoveruser"
    test_email = "testrecover@example.com"
    test_password = "recoverPassword123"

    async with TestSessionFactory() as session:
        await create_test_user_for_password_reset(session, test_username, test_email, test_password)

    response = await client.post(f"{settings.API_V1_STR}/password-recovery/{test_username}")

    assert response.status_code == 201
    token_data = response.json()
    assert token_data["username"] == test_username
    assert "reset_token" in token_data
    assert "expires_at" in token_data
    reset_token_str = token_data["reset_token"]

    # Verify token in DB
    async with TestSessionFactory() as session:
        token_obj = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == reset_token_str)
        )
        db_token = token_obj.scalars().first()
        assert db_token is not None
        assert db_token.used is False
        user_in_db = await crud_user.get_by_username(session, username=test_username)
        assert db_token.user_id == user_in_db.id

@pytest.mark.asyncio
async def test_recover_password_generate_token_user_not_found(
    client: httpx.AsyncClient,
) -> None:
    """Test password recovery for a non-existent username."""
    non_existent_username = "nosuchuser"
    response = await client.post(f"{settings.API_V1_STR}/password-recovery/{non_existent_username}")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]

# --- Test Cases for POST /reset-password/ ---

@pytest.mark.asyncio
async def test_reset_password_success(
    client: httpx.AsyncClient,
) -> None:
    """Test successful password reset with a valid token."""
    test_username = "testresetuser"
    test_email = "testreset@example.com"
    original_password = "originalPassword123"
    new_password = "newPassword456"

    async with TestSessionFactory() as session:
        user = await create_test_user_for_password_reset(session, test_username, test_email, original_password)

    # 1. Generate token
    gen_response = await client.post(f"{settings.API_V1_STR}/password-recovery/{test_username}")
    assert gen_response.status_code == 201
    reset_token = gen_response.json()["reset_token"]

    # 2. Reset password
    reset_payload = {"token": reset_token, "new_password": new_password}
    reset_response = await client.post(f"{settings.API_V1_STR}/reset-password/", json=reset_payload)
    
    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "Password updated successfully"

    # 3. Verify password changed (e.g., by checking hash or trying to log in)
    async with TestSessionFactory() as session:
        user_after_reset = await crud_user.get_by_username(session, username=test_username)
        assert user_after_reset is not None
        assert security.verify_password(new_password, user_after_reset.hashed_password) is True
        assert security.verify_password(original_password, user_after_reset.hashed_password) is False

        # Verify token is marked as used
        token_obj = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == reset_token)
        )
        db_token = token_obj.scalars().first()
        assert db_token is not None
        assert db_token.used is True


@pytest.mark.asyncio
async def test_reset_password_invalid_token(
    client: httpx.AsyncClient,
) -> None:
    """Test password reset with an invalid/non-existent token."""
    reset_payload = {"token": "thisisafaketoken", "new_password": "someNewPassword123"}
    response = await client.post(f"{settings.API_V1_STR}/reset-password/", json=reset_payload)
    assert response.status_code == 400
    assert "Invalid password reset token" in response.json()["detail"]

@pytest.mark.asyncio
async def test_reset_password_expired_token(
    client: httpx.AsyncClient,
) -> None:
    """Test password reset with an expired token."""
    test_username = "testexpiredtokenuser"
    test_email = "testexpired@example.com"
    password = "expiredPassword123"
    new_password = "newPasswordForExpired"

    async with TestSessionFactory() as session:
        user = await create_test_user_for_password_reset(session, test_username, test_email, password)
        
        # Generate token via API first
        gen_response = await client.post(f"{settings.API_V1_STR}/password-recovery/{test_username}")
        assert gen_response.status_code == 201
        reset_token_str = gen_response.json()["reset_token"]

        # Now, manually expire the token in DB
        token_obj_result = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == reset_token_str)
        )
        token_obj = token_obj_result.scalars().first()
        assert token_obj is not None
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(hours=2) # Expired 2 hours ago
        session.add(token_obj)
        await session.commit()

    reset_payload = {"token": reset_token_str, "new_password": new_password}
    response = await client.post(f"{settings.API_V1_STR}/reset-password/", json=reset_payload)
    assert response.status_code == 400
    assert "invalid or has expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_used_token(
    client: httpx.AsyncClient,
) -> None:
    """Test password reset attempt with an already used token."""
    test_username = "testusedtokenuser"
    test_email = "testusedtoken@example.com"
    original_password = "originalUsedPassword123"
    new_password1 = "newPasswordUsed1"
    new_password2 = "newPasswordUsed2"

    async with TestSessionFactory() as session:
        await create_test_user_for_password_reset(session, test_username, test_email, original_password)

    # 1. Generate token
    gen_response = await client.post(f"{settings.API_V1_STR}/password-recovery/{test_username}")
    assert gen_response.status_code == 201
    reset_token = gen_response.json()["reset_token"]

    # 2. Reset password (first, successful use)
    reset_payload1 = {"token": reset_token, "new_password": new_password1}
    reset_response1 = await client.post(f"{settings.API_V1_STR}/reset-password/", json=reset_payload1)
    assert reset_response1.status_code == 200

    # 3. Attempt to reset password again with the same token
    reset_payload2 = {"token": reset_token, "new_password": new_password2}
    reset_response2 = await client.post(f"{settings.API_V1_STR}/reset-password/", json=reset_payload2)
    assert reset_response2.status_code == 400
    assert "invalid or has expired" in reset_response2.json()["detail"].lower() # API uses same message for used/expired

@pytest.mark.asyncio
async def test_reset_password_new_password_too_short(
    client: httpx.AsyncClient,
) -> None:
    """Test password reset with a new password that is too short."""
    test_username = "testshortpwuser"
    test_email = "testshortpw@example.com"
    original_password = "shortPwOriginal123"
    short_new_password = "short" # Less than 8 chars

    async with TestSessionFactory() as session:
        await create_test_user_for_password_reset(session, test_username, test_email, original_password)

    # 1. Generate token
    gen_response = await client.post(f"{settings.API_V1_STR}/password-recovery/{test_username}")
    assert gen_response.status_code == 201
    reset_token = gen_response.json()["reset_token"]

    # 2. Attempt to reset password with short new password
    reset_payload = {"token": reset_token, "new_password": short_new_password}
    reset_response = await client.post(f"{settings.API_V1_STR}/reset-password/", json=reset_payload)
    
    # Expecting 422 Unprocessable Entity due to Pydantic validation on ResetPasswordRequest model
    assert reset_response.status_code == 422 
    # The exact error message structure can vary with FastAPI/Pydantic versions
    # Typically it's a list of errors under "detail"
    error_details = reset_response.json().get("detail", [])
    found_password_error = False
    for error in error_details:
        if error.get("loc") and "new_password" in error.get("loc") and "type" in error and "string_too_short" in error.get("type"):
            found_password_error = True
            break
    assert found_password_error, "Did not find specific error for new_password being too short."

# Note: Test for "mismatched new passwords" is not applicable as the API endpoint
# `POST /reset-password/` and its Pydantic model `ResetPasswordRequest`
# only accept `new_password` and do not have a field for password confirmation.
# This kind of check is typically handled by the frontend.

# Note: The crud.password_reset_token module was assumed. If it doesn't exist,
# direct DB operations on PasswordResetToken model are used (as shown in tests).
# The `create_test_user_for_password_reset` helper also uses direct model creation
# for simplicity, assuming `crud_user.create` might have complexities not needed here.
print("test_password_reset.py created with tests for password recovery and reset endpoints.")
