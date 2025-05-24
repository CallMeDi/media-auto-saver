# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import select, Session, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
import os # Added import
from typing import List, Optional, Type, TypeVar, Generic, Any
from pydantic import BaseModel
from datetime import datetime, timezone # 导入 timezone / Import timezone

from app.core.config import PROJECT_ROOT # Added import
from app.models.link import Link, LinkCreate, LinkUpdate, LinkStatus

# 中文: 定义泛型类型变量, 用于 CRUD 操作的基类
# English: Define generic type variables for the base CRUD class
USER_COOKIES_BASE_DIR_NAME = "user_cookies" # Added constant

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    中文: 提供基本 CRUD 操作的基类。
    English: Base class providing basic CRUD operations.

    参数 / Parameters:
        model: SQLModel 模型类 / A SQLModel model class
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        中文: 通过 ID 获取单个对象。
        English: Get a single object by ID.
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[List[Any]] = None # 新增排序参数 / Added order_by parameter
    ) -> List[ModelType]:
        """
        中文: 获取多个对象 (支持分页和排序)。
        English: Get multiple objects (with pagination and sorting support).
        """
        query = select(self.model)
        if order_by is not None:
            # 应用排序条件 / Apply order conditions
            # 例如: order_by=[self.model.timestamp.desc()]
            # Example: order_by=[self.model.timestamp.desc()]
            query = query.order_by(*order_by)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        中文: 创建新对象。
        English: Create a new object.
        """
        # 中文: 使用 Pydantic 模型的 model_dump 方法将输入数据转换为字典
        # English: Use Pydantic model's model_dump method to convert input data to a dictionary
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        中文: 更新现有对象.
        English: Update an existing object.
        """
        # 中文: 将数据库对象转换为字典
        # English: Convert the database object to a dictionary
        obj_data = db_obj.model_dump()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # 中文: 使用 Pydantic 模型的 model_dump 方法, exclude_unset=True 表示只包含显式设置的字段
            # English: Use Pydantic model's model_dump method, exclude_unset=True means only include explicitly set fields
            update_data = obj_in.model_dump(exclude_unset=True)

        # 中文: 遍历更新数据, 更新数据库对象的字段
        # English: Iterate through update data and update the database object's fields
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        # 中文: 特殊处理 updated_at 字段
        # English: Special handling for the updated_at field
        if hasattr(db_obj, "updated_at"):
             setattr(db_obj, "updated_at", datetime.now(timezone.utc)) # 使用 aware datetime / Use aware datetime

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        中文: 通过 ID 删除对象。
        English: Remove an object by ID.
        """
        obj = await self.get(db=db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj


class CRUDLink(CRUDBase[Link, LinkCreate, LinkUpdate]):
    """
    中文: Link 模型的特定 CRUD 操作。
    English: Specific CRUD operations for the Link model.
    """

    def _validate_and_normalize_cookies_path(self, user_path: Optional[str]) -> Optional[str]:
        if not user_path:
            return None

        # Disallow absolute paths from user input
        if os.path.isabs(user_path):
            raise ValueError("cookies_path must be a relative path, not an absolute path.")

        # Normalize the user-provided path (e.g., collapses ../, ./, normalizes slashes)
        # Treat user_path as a filename or path relative to USER_COOKIES_BASE_DIR_NAME
        normalized_filename = os.path.normpath(user_path)

        # After normalization, check for attempts to go outside the intended directory
        if normalized_filename.startswith("..") or "/../" in normalized_filename or "\\../" in normalized_filename:
            raise ValueError("cookies_path attempts directory traversal.")
        
        # The path stored in DB should just be the filename or relative path within the base dir
        # e.g., "my_cookie.txt" or "subdir/my_cookie.txt"
        
        # Construct the full path for validation
        # Base directory for user cookies
        cookies_base_dir = os.path.join(PROJECT_ROOT, USER_COOKIES_BASE_DIR_NAME)
        
        # Ensure cookies_base_dir exists (optional: create if not, but for now assume it's manually created or handled elsewhere)
        # os.makedirs(cookies_base_dir, exist_ok=True) 

        full_path_to_check = os.path.join(cookies_base_dir, normalized_filename)
        full_path_to_check = os.path.normpath(full_path_to_check) # Normalize again after join

        # Final security check: ensure the resolved path is actually within cookies_base_dir
        if os.path.commonpath([cookies_base_dir]) != os.path.commonpath([cookies_base_dir, full_path_to_check]):
            raise ValueError("cookies_path resolves outside the designated cookies directory.")

        if not os.path.exists(full_path_to_check):
            raise ValueError(f"Specified cookies file does not exist at resolved path: {normalized_filename} (expected under {USER_COOKIES_BASE_DIR_NAME})")
        
        if not os.path.isfile(full_path_to_check):
            raise ValueError(f"Specified cookies_path is not a file: {normalized_filename}")

        # Return the clean, normalized filename/relative path to be stored in DB
        return normalized_filename

    async def create(self, db: AsyncSession, *, obj_in: LinkCreate) -> Link:
        obj_in_data = obj_in.model_dump()
        if "cookies_path" in obj_in_data and obj_in_data["cookies_path"] is not None:
            try:
                obj_in_data["cookies_path"] = self._validate_and_normalize_cookies_path(obj_in_data["cookies_path"])
            except ValueError as e:
                # This exception should be caught by the API layer to return HTTP 400
                raise e 
        
        # The rest of the original create method from CRUDBase
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Link,
        obj_in: LinkUpdate | dict[str, Any]
    ) -> Link:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "cookies_path" in update_data: # Handles explicit None to clear path too
            if update_data["cookies_path"] is not None:
                try:
                    update_data["cookies_path"] = self._validate_and_normalize_cookies_path(update_data["cookies_path"])
                except ValueError as e:
                    # This exception should be caught by the API layer to return HTTP 400
                    raise e
            # If update_data["cookies_path"] is None, it will be set to None, effectively clearing the path

        # The rest of the original update method from CRUDBase
        # Convert the database object to a dictionary
        obj_data = db_obj.model_dump() # This line was missing from the provided snippet for update, adding it back from CRUDBase
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        if hasattr(db_obj, "updated_at"):
            setattr(db_obj, "updated_at", datetime.now(timezone.utc))
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_url(self, db: AsyncSession, *, url: str) -> Optional[Link]:
        """
        中文: 通过 URL 获取链接。
        English: Get a link by URL.
        """
        result = await db.execute(select(Link).where(Link.url == url))
        return result.scalars().first()

    async def get_enabled_links(self, db: AsyncSession, *, link_type: Optional[str] = None) -> List[Link]:
        """
        中文: 获取所有启用的链接, 可选按类型过滤。
        English: Get all enabled links, optionally filtered by type.
        """
        query = select(Link).where(Link.is_enabled == True)
        if link_type:
            query = query.where(Link.link_type == link_type)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_status(
        self,
        db: AsyncSession,
        *,
        db_obj: Link,
        status: LinkStatus,
        error_message: Optional[str] = None,
        is_success: bool = False # 新增参数, 指示操作是否成功 / Added parameter to indicate if the operation was successful
    ) -> Link:
        """
        中文: 更新链接的状态、错误信息和相关时间戳。
        English: Update the status, error message, and relevant timestamps of a link.

        参数 / Parameters:
            db: 数据库会话 / Database session.
            db_obj: 要更新的链接对象 / The link object to update.
            status: 新的状态 / The new status.
            error_message: 错误信息 (仅在 status 为 ERROR 时设置) / Error message (only set if status is ERROR).
            is_success: 操作是否成功完成 (用于更新 last_success_at) / Whether the operation completed successfully (for updating last_success_at).
        """
        update_data = {
            "status": status,
            "last_checked_at": datetime.now(timezone.utc) # 总是更新检查时间 / Always update check time
        }
        if status == LinkStatus.ERROR:
            update_data["error_message"] = error_message
        else:
            # 中文: 如果状态不是错误, 清除错误信息
            # English: If the status is not error, clear the error message
            update_data["error_message"] = None

        # 中文: 仅在显式成功时更新 last_success_at
        # English: Only update last_success_at on explicit success
        if is_success:
            update_data["last_success_at"] = datetime.now(timezone.utc)

        return await self.update(db=db, db_obj=db_obj, obj_in=update_data)

# 中文: 创建 Link CRUD 操作的实例
# English: Create an instance of the Link CRUD operations
link = CRUDLink(Link)
