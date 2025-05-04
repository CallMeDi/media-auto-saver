# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, List, Any, Dict # 导入 Dict / Import Dict
from datetime import datetime, timezone
from sqlalchemy import JSON # 使用 SQLAlchemy 的 JSON 类型 / Use SQLAlchemy's JSON type
import enum

# 中文: 导入 Link 模型用于建立关系 (如果需要)
# English: Import Link model for relationship (if needed)
# from .link import Link # 暂时不建立直接关系, 避免循环导入 / Avoid direct relationship for now to prevent circular imports

class HistoryStatus(str, enum.Enum):
    """
    中文: 历史记录状态枚举
    English: History record status enumeration
    """
    SUCCESS = "success" # 成功 / Success
    FAILURE = "failure" # 失败 / Failure

class HistoryLogBase(SQLModel):
    """
    中文: 历史记录模型的基础字段
    English: Base fields for the HistoryLog model
    """
    link_id: int = Field(foreign_key="link.id", index=True, description="关联的链接 ID / Associated Link ID")
    # 中文: 使用 timezone.utc 确保时间戳是 aware 的 / Use timezone.utc to ensure timestamp is aware
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True, description="事件发生时间 / Event timestamp")
    status: HistoryStatus = Field(description="任务状态 (成功/失败) / Task status (success/failure)")
    # 中文: 存储下载/录制的文件路径列表 (JSON)
    # English: Store list of downloaded/recorded file paths (JSON)
    downloaded_files: Optional[List[str]] = Field(default=None, sa_column=Column(JSON), description="下载/录制的文件列表 / List of downloaded/recorded files")
    error_message: Optional[str] = Field(default=None, description="错误信息 (如果失败) / Error message (if failed)")
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="其他详细信息 (例如文件大小, 时长等) / Other details (e.g., file size, duration, etc.)")

class HistoryLog(HistoryLogBase, table=True):
    """
    中文: 历史记录数据库表模型
    English: HistoryLog database table model
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # 中文: 定义与 Link 模型的关系 (可选, 用于 ORM 查询)
    # English: Define relationship with Link model (optional, for ORM queries)
    # link: Optional["Link"] = Relationship(back_populates="history_logs") # 需要在 Link 模型中添加 back_populates / Requires adding back_populates in Link model

class HistoryLogRead(HistoryLogBase):
    """
    中文: 读取历史记录时使用的 Pydantic 模型
    English: Pydantic model used when reading a history log
    """
    id: int
    timestamp: datetime # 确保时间戳被正确序列化 / Ensure timestamp is serialized correctly

class HistoryLogCreate(HistoryLogBase):
    """
    中文: 创建历史记录时使用的 Pydantic 模型
    English: Pydantic model used when creating a history log
    """
    pass
