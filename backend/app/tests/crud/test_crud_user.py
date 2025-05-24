# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
from unittest import mock
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserCreate, UserUpdate
from app.crud.crud_user import user as crud_user_instance # instance
from app.crud import crud_user as crud_user_module # For patching module-level functions
from app.core import security as core_security_module # For patching security functions
from app.tests.conftest import TestSessionFactory # For DB interaction

MOCKED_HASHED_PASSWORD = "mocked_hashed_password_string"
NEW_MOCKED_HASHED_PASSWORD = "new_mocked_hashed_password_string"

# --- Helper Fixture for Creating Users (without relying on crud_user.create for setup) ---

@pytest.fixture
async def create_raw_user_in_db(db: AsyncSession) -> User:
    """
    Helper to create a user directly in the DB for fetching/updating,
    bypassing the CRUD create method for initial setup in some tests.
    """
    user_data = {
        "username": f"raw_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "email": f"raw_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}@example.com",
        "hashed_password": "initial_raw_hashed_password",
        "is_active": True,
        "is_superuser": False,
    }
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- Tests for get_by_username ---

@pytest.mark.asyncio
async def test_get_by_username_existing(db: AsyncSession, create_raw_user_in_db: User):
    """Test fetching an existing user by username."""
    raw_user = create_raw_user_in_db
    fetched_user = await crud_user_instance.get_by_username(db=db, username=raw_user.username)
    assert fetched_user is not None
    assert fetched_user.id == raw_user.id
    assert fetched_user.username == raw_user.username

@pytest.mark.asyncio
async def test_get_by_username_non_existent(db: AsyncSession):
    """Test fetching a non-existent username."""
    fetched_user = await crud_user_instance.get_by_username(db=db, username="nonexistentuser")
    assert fetched_user is None

# --- Tests for overridden create method ---

@pytest.mark.asyncio
@mock.patch.object(core_security_module, "get_password_hash", return_value=MOCKED_HASHED_PASSWORD)
async def test_create_user(mock_get_password_hash, db: AsyncSession):
    """Test creating a user with password hashing."""
    user_in_data = UserCreate(
        username="newuser",
        email="newuser@example.com",
        password="plainPassword123",
        full_name="New User Fullname",
        is_active=True,
        is_superuser=False
    )
    
    created_user = await crud_user_instance.create(db=db, obj_in=user_in_data)

    mock_get_password_hash.assert_called_once_with(user_in_data.password)
    
    assert created_user.id is not None
    assert created_user.username == user_in_data.username
    assert created_user.email == user_in_data.email
    assert created_user.full_name == user_in_data.full_name
    assert created_user.is_active == user_in_data.is_active
    assert created_user.is_superuser == user_in_data.is_superuser
    assert created_user.hashed_password == MOCKED_HASHED_PASSWORD

    # Verify in DB
    db_user = await db.get(User, created_user.id)
    assert db_user is not None
    assert db_user.hashed_password == MOCKED_HASHED_PASSWORD

# --- Tests for overridden update method ---

@pytest.mark.asyncio
async def test_update_user_no_password_change(db: AsyncSession, create_raw_user_in_db: User):
    """Test updating user attributes without changing the password."""
    raw_user = create_raw_user_in_db
    original_hashed_password = raw_user.hashed_password
    
    update_data = UserUpdate(
        email="updated.email@example.com",
        is_active=False,
        full_name="Updated Full Name"
    )
    
    updated_user = await crud_user_instance.update(db=db, db_obj=raw_user, obj_in=update_data)

    assert updated_user.id == raw_user.id
    assert updated_user.email == update_data.email
    assert updated_user.is_active == update_data.is_active
    assert updated_user.full_name == update_data.full_name
    assert updated_user.hashed_password == original_hashed_password # Password should not change

@pytest.mark.asyncio
@mock.patch.object(core_security_module, "get_password_hash", return_value=NEW_MOCKED_HASHED_PASSWORD)
async def test_update_user_password_only(mock_get_password_hash, db: AsyncSession, create_raw_user_in_db: User):
    """Test updating only the user's password."""
    raw_user = create_raw_user_in_db
    new_plain_password = "newPlainPassword456"
    
    update_data = UserUpdate(password=new_plain_password)
    
    updated_user = await crud_user_instance.update(db=db, db_obj=raw_user, obj_in=update_data)

    mock_get_password_hash.assert_called_once_with(new_plain_password)
    assert updated_user.hashed_password == NEW_MOCKED_HASHED_PASSWORD

@pytest.mark.asyncio
@mock.patch.object(core_security_module, "get_password_hash", return_value=NEW_MOCKED_HASHED_PASSWORD)
async def test_update_user_password_and_other_attributes(mock_get_password_hash, db: AsyncSession, create_raw_user_in_db: User):
    """Test updating password and other attributes simultaneously."""
    raw_user = create_raw_user_in_db
    new_plain_password = "anotherNewPassword789"
    
    update_data_dict = { # Using dict to test that path in update method too
        "password": new_plain_password,
        "email": "super.updated.email@example.net",
        "is_superuser": True
    }
    
    updated_user = await crud_user_instance.update(db=db, db_obj=raw_user, obj_in=update_data_dict)

    mock_get_password_hash.assert_called_once_with(new_plain_password)
    assert updated_user.hashed_password == NEW_MOCKED_HASHED_PASSWORD
    assert updated_user.email == update_data_dict["email"]
    assert updated_user.is_superuser == update_data_dict["is_superuser"]


# --- Tests for authenticate ---

@pytest.mark.asyncio
async def test_authenticate_correct_credentials(db: AsyncSession):
    """Test authentication with correct username and password."""
    username = "auth_user_correct"
    plain_password = "authPasswordCorrect"
    
    # Create user with a known (mocked) hashed password
    with mock.patch.object(core_security_module, "get_password_hash", return_value=MOCKED_HASHED_PASSWORD):
        user_in = UserCreate(username=username, email="auth_correct@example.com", password=plain_password)
        await crud_user_instance.create(db=db, obj_in=user_in)

    # Mock verify_password to return True for these credentials
    with mock.patch.object(core_security_module, "verify_password", return_value=True) as mock_verify:
        authenticated_user = await crud_user_instance.authenticate(db=db, username=username, password=plain_password)
    
    assert authenticated_user is not None
    assert authenticated_user.username == username
    mock_verify.assert_called_once_with(plain_password, MOCKED_HASHED_PASSWORD)

@pytest.mark.asyncio
async def test_authenticate_incorrect_password(db: AsyncSession):
    """Test authentication with incorrect password."""
    username = "auth_user_incorrect_pw"
    correct_plain_password = "authPasswordCorrect2"
    incorrect_plain_password = "authPasswordIncorrect2"

    with mock.patch.object(core_security_module, "get_password_hash", return_value=MOCKED_HASHED_PASSWORD):
        user_in = UserCreate(username=username, email="auth_incorrect_pw@example.com", password=correct_plain_password)
        await crud_user_instance.create(db=db, obj_in=user_in)

    # Mock verify_password to return False
    with mock.patch.object(core_security_module, "verify_password", return_value=False) as mock_verify:
        authenticated_user = await crud_user_instance.authenticate(db=db, username=username, password=incorrect_plain_password)
        
    assert authenticated_user is None
    mock_verify.assert_called_once_with(incorrect_plain_password, MOCKED_HASHED_PASSWORD)

@pytest.mark.asyncio
async def test_authenticate_non_existent_username(db: AsyncSession):
    """Test authentication with a non-existent username."""
    # verify_password should not even be called if user is not found
    with mock.patch.object(core_security_module, "verify_password") as mock_verify:
        authenticated_user = await crud_user_instance.authenticate(db=db, username="no_such_auth_user", password="anypassword")
    
    assert authenticated_user is None
    mock_verify.assert_not_called()

# --- Tests for is_active and is_superuser ---

def test_is_active():
    """Test the is_active utility method."""
    active_user = User(username="active_test", hashed_password="pw", is_active=True)
    inactive_user = User(username="inactive_test", hashed_password="pw", is_active=False)
    
    assert crud_user_instance.is_active(active_user) is True
    assert crud_user_instance.is_active(inactive_user) is False

def test_is_superuser():
    """Test the is_superuser utility method."""
    superuser = User(username="super_test", hashed_password="pw", is_superuser=True)
    regular_user = User(username="regular_test", hashed_password="pw", is_superuser=False)
    
    assert crud_user_instance.is_superuser(superuser) is True
    assert crud_user_instance.is_superuser(regular_user) is False

# Note: CRUDBase generic methods (get, get_multi, remove) are assumed to be
# covered by other CRUD tests like test_crud_history or test_crud_link.
# The focus here is on User-specific overridden methods and utility functions.

print("test_crud_user.py created with CRUD tests for User.")
