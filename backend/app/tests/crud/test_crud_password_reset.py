# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
from unittest import mock
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserCreate # Assuming User model is in app.models.user
from app.models.password_reset import PasswordResetToken, PasswordResetTokenCreate
from app.crud.crud_user import user as crud_user # To create prerequisite User objects
from app.crud.crud_password_reset import password_reset_token as crud_pr_token_instance
from app.crud import crud_password_reset as crud_pr_module # For patching module-level functions
from app.models import password_reset as model_pr_module # For patching model-level functions
from app.tests.conftest import TestSessionFactory # For DB interaction
from app.core.security import get_password_hash # For creating users

# --- Helper Fixture for Creating Users ---

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Fixture to create a test User in the database."""
    user_in = UserCreate(
        username=f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S%f')}", # Unique username
        email=f"test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}@example.com", # Unique email
        password="testPassword123"
    )
    # Use the actual crud_user.create method
    # If crud_user.create is synchronous, adapt or use a direct User model creation
    # For this example, assume crud_user.create exists and is async, or use a simplified creation:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- Tests for CRUDPasswordResetToken specific methods ---

MOCKED_TOKEN_STR = "mocked_fixed_reset_token_string"
MOCKED_FUTURE_DATETIME = datetime.now(timezone.utc) + timedelta(hours=1)
MOCKED_PAST_DATETIME = datetime.now(timezone.utc) - timedelta(hours=1)
MOCKED_NOW_DATETIME = datetime.now(timezone.utc) # For checking 'now' updates

@pytest.mark.asyncio
@mock.patch.object(model_pr_module, "generate_reset_token", return_value=MOCKED_TOKEN_STR)
@mock.patch.object(model_pr_module, "calculate_expiry_date", return_value=MOCKED_FUTURE_DATETIME)
async def test_create_reset_token(
    mock_generate_token,
    mock_calculate_expiry,
    db: AsyncSession,
    test_user: User
):
    """Test creating a password reset token."""
    created_token_obj = await crud_pr_token_instance.create_reset_token(db=db, user_id=test_user.id)

    mock_generate_token.assert_called_once()
    mock_calculate_expiry.assert_called_once()

    assert created_token_obj.id is not None
    assert created_token_obj.user_id == test_user.id
    assert created_token_obj.token == MOCKED_TOKEN_STR
    assert created_token_obj.expires_at == MOCKED_FUTURE_DATETIME
    assert created_token_obj.used is False

    # Verify it's in the DB
    db_token = await db.get(PasswordResetToken, created_token_obj.id)
    assert db_token is not None
    assert db_token.token == MOCKED_TOKEN_STR
    assert db_token.user_id == test_user.id


@pytest.mark.asyncio
@mock.patch.object(model_pr_module, "generate_reset_token", return_value=MOCKED_TOKEN_STR)
@mock.patch.object(model_pr_module, "calculate_expiry_date", return_value=MOCKED_FUTURE_DATETIME)
async def test_get_by_token(
    mock_generate_token,
    mock_calculate_expiry,
    db: AsyncSession,
    test_user: User
):
    """Test fetching a token by its string."""
    # Create a token first
    original_token_obj = await crud_pr_token_instance.create_reset_token(db=db, user_id=test_user.id)

    # Fetch it
    fetched_token_obj = await crud_pr_token_instance.get_by_token(db=db, token=MOCKED_TOKEN_STR)
    assert fetched_token_obj is not None
    assert fetched_token_obj.id == original_token_obj.id
    assert fetched_token_obj.token == MOCKED_TOKEN_STR

    # Attempt to fetch non-existent token
    non_existent_token_obj = await crud_pr_token_instance.get_by_token(db=db, token="non_existent_fake_token")
    assert non_existent_token_obj is None


@pytest.mark.asyncio
@mock.patch.object(model_pr_module, "datetime") # Patch datetime within the model module
async def test_use_token(
    mock_model_datetime, # Patched datetime.now in model_pr_module
    db: AsyncSession,
    test_user: User
):
    """Test marking a token as used."""
    # Configure the mock for datetime.now(timezone.utc)
    mock_model_datetime.now.return_value = MOCKED_NOW_DATETIME
    
    # Create a token (use default mocks for generate/calculate for simplicity here, or re-patch)
    with mock.patch.object(model_pr_module, "generate_reset_token", return_value="another_token"), \
         mock.patch.object(model_pr_module, "calculate_expiry_date", return_value=MOCKED_FUTURE_DATETIME):
        token_to_use = await crud_pr_token_instance.create_reset_token(db=db, user_id=test_user.id)

    assert token_to_use.used is False
    assert token_to_use.expires_at == MOCKED_FUTURE_DATETIME # Initial expiry

    used_token_obj = await crud_pr_token_instance.use_token(db=db, token_obj=token_to_use)

    assert used_token_obj.used is True
    # Verify expires_at is updated to 'now'
    # The crud_password_reset.use_token calls datetime.now(timezone.utc) directly
    # So, we need to patch datetime.now in the crud_pr_module or globally.
    # The `mock_model_datetime` above patches it in the `app.models.password_reset` module.
    # The `use_token` function in `app.crud.crud_password_reset` uses `datetime.now(timezone.utc)`.
    # So, we need to patch it in `app.crud.crud_password_reset`.
    
    with mock.patch.object(crud_pr_module, "datetime") as mock_crud_datetime: # Patch datetime in crud_pr_module
        mock_crud_datetime.now.return_value = MOCKED_NOW_DATETIME
        # Re-fetch and call use_token again with this specific mock active
        token_to_use_again = await db.get(PasswordResetToken, token_to_use.id) # Re-fetch fresh object
        refreshed_used_token_obj = await crud_pr_token_instance.use_token(db=db, token_obj=token_to_use_again)
        
        assert refreshed_used_token_obj.expires_at == MOCKED_NOW_DATETIME
        mock_crud_datetime.now.assert_called_once_with(timezone.utc)


@pytest.mark.asyncio
async def test_is_token_valid(db: AsyncSession, test_user: User):
    """Test token validity checks."""
    # 1. Fresh token (not used, future expiry)
    with mock.patch.object(model_pr_module, "generate_reset_token", return_value="valid_token"), \
         mock.patch.object(model_pr_module, "calculate_expiry_date", return_value=MOCKED_FUTURE_DATETIME):
        fresh_token = await crud_pr_token_instance.create_reset_token(db=db, user_id=test_user.id)
    assert crud_pr_token_instance.is_token_valid(fresh_token) is True

    # 2. Used token
    used_token = await crud_pr_token_instance.use_token(db=db, token_obj=fresh_token) # This also expires it
    assert crud_pr_token_instance.is_token_valid(used_token) is False # Should be false because it's used AND expired by use_token

    # 3. Expired token (not used)
    with mock.patch.object(model_pr_module, "generate_reset_token", return_value="expired_token_str"), \
         mock.patch.object(model_pr_module, "calculate_expiry_date", return_value=MOCKED_PAST_DATETIME): # Expires in the past
        expired_token = await crud_pr_token_instance.create_reset_token(db=db, user_id=test_user.id)
    assert crud_pr_token_instance.is_token_valid(expired_token) is False

    # 4. Token that is both used and expired (already covered by #2, but for clarity)
    # Let's create one manually that's used, and has a past expiry different from 'now'
    manually_used_expired = PasswordResetToken(
        token="manual_used_expired",
        user_id=test_user.id,
        expires_at=MOCKED_PAST_DATETIME,
        used=True
    )
    db.add(manually_used_expired)
    await db.commit()
    await db.refresh(manually_used_expired)
    assert crud_pr_token_instance.is_token_valid(manually_used_expired) is False
    
    # 5. Test timezone handling (naive vs aware)
    # Create a token, its expires_at should be aware (due to model definition with DateTime(timezone=True))
    # and calculate_expiry_date returning aware datetime.
    # SQLModel/SQLAlchemy should handle this. We are mostly testing the `is_token_valid` logic.
    
    token_for_tz_test = PasswordResetToken(
        token="tz_test_token",
        user_id=test_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=1), # Create a NAIVE datetime but in UTC
        used=False
    )
    # The model field `expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))`
    # should ensure it's stored as timezone-aware or converted appropriately by the DB driver.
    # When read back, it should ideally be aware.
    # If not, `is_token_valid` has a fallback to make it aware.

    db.add(token_for_tz_test)
    await db.commit()
    await db.refresh(token_for_tz_test) # token_for_tz_test.expires_at might be naive or aware here

    # Ensure the test logic inside is_token_valid correctly handles it
    # The line `if expires_at_aware.tzinfo is None: expires_at_aware = expires_at_aware.replace(tzinfo=timezone.utc)`
    # is the one we are implicitly testing.
    
    # To force a naive datetime for expires_at to test the specific if block:
    mock_token_naive_expiry = mock.Mock(spec=PasswordResetToken)
    mock_token_naive_expiry.used = False
    mock_token_naive_expiry.expires_at = datetime.utcnow() + timedelta(hours=1) # Naive datetime

    with mock.patch.object(crud_pr_module, "datetime") as mock_crud_dt_for_is_valid: # Patch datetime.now in crud_pr_module
        # Make "now" well before the naive token's expiry
        mock_crud_dt_for_is_valid.now.return_value = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=30)
        assert crud_pr_token_instance.is_token_valid(mock_token_naive_expiry) is True

        # Make "now" well after the naive token's expiry
        mock_crud_dt_for_is_valid.now.return_value = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(hours=2)
        assert crud_pr_token_instance.is_token_valid(mock_token_naive_expiry) is False

print("test_crud_password_reset.py created with CRUD tests for PasswordResetToken.")
