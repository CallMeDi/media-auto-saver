# -*- coding: utf-8 -*-
# /usr/bin/env python3

from sqlmodel import SQLModel, Field, Column
from typing import Optional, Dict, Any
from datetime import datetime, timezone # 导入 timezone / Import timezone
import enum
from sqlalchemy import JSON # 使用 SQLAlchemy 的 JSON 类型 / Use SQLAlchemy's JSON type

class LinkType(str, enum.Enum):
    """
    中文: 链接类型枚举
    English: Link type enumeration
    """
    CREATOR = "creator" # 创作者链接 / Creator link
    LIVE = "live"       # 直播链接 / Live stream link

class LinkStatus(str, enum.Enum):
    """
    中文: 链接监控状态枚举
    English: Link monitoring status enumeration
    """
    IDLE = "idle"           # 空闲 / Idle
    MONITORING = "monitoring" # 监控中 / Monitoring
    DOWNLOADING = "downloading" # 下载中 / Downloading
    RECORDING = "recording"   # 录制中 / Recording
    ERROR = "error"         # 错误 / Error
    # DISABLED = "disabled" # 已移除, 使用 is_enabled=False 代替 / Removed, use is_enabled=False instead

class LinkBase(SQLModel):
    """
    中文: 链接模型的基础字段
    English: Base fields for the Link model
    """
    url: str = Field(index=True, unique=True, description="链接URL / Link URL")
    link_type: LinkType = Field(default=LinkType.CREATOR, description="链接类型 / Link type")
    site_name: Optional[str] = Field(default=None, index=True, description="网站名称 (例如: Twitter, YouTube) / Site name (e.g., Twitter, YouTube)")
    name: Optional[str] = Field(default=None, description="用户指定的名称或自动获取的名称 / User-specified or automatically fetched name")
    description: Optional[str] = Field(default=None, description="用户添加的描述 / User-added description")
    tags: Optional[str] = Field(default=None, description="用户添加的标签 (逗号分隔) / User-added tags (comma-separated)")
    status: LinkStatus = Field(default=LinkStatus.IDLE, description="当前状态 / Current status")
    last_checked_at: Optional[datetime] = Field(default=None, description="上次检查时间 / Last checked time")
    last_success_at: Optional[datetime] = Field(default=None, description="上次成功下载/录制时间 / Last successful download/record time")
    error_message: Optional[str] = Field(default=None, description="错误信息 / Error message")
    # 中文: 存储特定于链接的设置 (例如下载路径模板, 录制质量等)
    # English: Store link-specific settings (e.g., download path template, recording quality, etc.)
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON), description="特定设置 (JSON) / Specific settings (JSON)")
    # 中文: 用于传递给下载器的 Cookies 文件路径 (可选)
    # English: Path to the cookies file to pass to the downloader (optional)
    cookies_path: Optional[str] = Field(default=None, description="Cookies 文件路径 / Cookies file path")
    is_enabled: bool = Field(default=True, description="是否启用监控 / Whether monitoring is enabled")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间 / Creation time")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间 / Last update time")

class Link(LinkBase, table=True):
    """
    中文: 链接数据库表模型
    English: Link database table model
    """
    id: Optional[int] = Field(default=None, primary_key=True)

class LinkCreate(LinkBase):
    """
    中文: 创建链接时使用的 Pydantic 模型 (用于 API 输入验证)
    English: Pydantic model used when creating a link (for API input validation)
    """
    pass # 继承 LinkBase 的所有字段 / Inherits all fields from LinkBase

class LinkRead(LinkBase):
    """
    中文: 读取链接时使用的 Pydantic 模型 (用于 API 输出)
    English: Pydantic model used when reading a link (for API output)
    """
    id: int # 读取时必须包含 id / Must include id when reading

class LinkUpdate(SQLModel):
    """
    中文: 更新链接时使用的 Pydantic 模型 (所有字段可选)
    English: Pydantic model used when updating a link (all fields optional)
    """
    url: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[LinkStatus] = None
    error_message: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    cookies_path: Optional[str] = None # 允许更新 Cookies 路径 / Allow updating cookies path
    is_enabled: Optional[bool] = None
    # link_type 和 site_name 通常不应被更新 / link_type and site_name should generally not be updated
