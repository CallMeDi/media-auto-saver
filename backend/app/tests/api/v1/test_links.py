# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
from typing import Dict, List
import httpx
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Link, LinkRead, LinkType, LinkStatus # 导入相关模型 / Import related models
from app.tests.conftest import TestSessionFactory # 导入测试数据库会话工厂 / Import test DB session factory

# --- 辅助函数 / Helper Functions ---

async def create_test_link(client: httpx.AsyncClient, headers: Dict[str, str], url: str, name: str) -> Dict:
    """创建一个测试链接并返回其字典表示"""
    link_data = {
        "url": url,
        "link_type": LinkType.CREATOR,
        "name": name,
        "description": f"Desc for {name}",
        "tags": f"test,{name.lower()}",
    }
    response = await client.post(f"{settings.API_V1_STR}/links/", json=link_data, headers=headers)
    assert response.status_code == 201, f"Failed to create link: {response.text}"
    return response.json()

# --- 测试用例 / Test Cases ---

@pytest.mark.asyncio
async def test_create_link(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试创建新链接"""
    url = "https://example.com/creator/test_create"
    name = "Test Create Link"
    link_data = {
        "url": url,
        "link_type": LinkType.CREATOR,
        "name": name,
        "description": "Testing link creation",
        "tags": "test,create",
        "cookies_path": "path/to/cookies.txt", # 测试 cookies_path 字段 / Test cookies_path field
        "settings": {"quality": "high"}
    }
    response = await client.post(f"{settings.API_V1_STR}/links/", json=link_data, headers=superuser_token_headers)
    assert response.status_code == 201
    created_link = response.json()
    assert created_link["url"] == url
    assert created_link["name"] == name
    assert created_link["site_name"] == "Example" # 基于 extract_site_name / Based on extract_site_name
    assert created_link["cookies_path"] == "path/to/cookies.txt"
    assert created_link["settings"]["quality"] == "high"
    assert "id" in created_link

@pytest.mark.asyncio
async def test_create_link_duplicate_url(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试创建具有重复 URL 的链接"""
    url = "https://example.com/creator/duplicate"
    await create_test_link(client, superuser_token_headers, url, "First Duplicate")

    # 尝试再次创建相同 URL 的链接 / Try creating link with the same URL again
    link_data = {"url": url, "name": "Second Duplicate"}
    response = await client.post(f"{settings.API_V1_STR}/links/", json=link_data, headers=superuser_token_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_links(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试读取链接列表"""
    # 先清空可能存在的链接 (因为测试数据库是 session 范围的)
    # Clear existing links first (as test DB is session-scoped)
    async with TestSessionFactory() as session:
         result = await session.execute(select(Link))
         all_links = result.scalars().all()
         for link in all_links:
             await session.delete(link)
         await session.commit()

    # 创建一些测试链接 / Create some test links
    link1 = await create_test_link(client, superuser_token_headers, "https://example.com/link1", "Link 1")
    link2 = await create_test_link(client, superuser_token_headers, "https://anothersite.org/link2", "Link 2")

    response = await client.get(f"{settings.API_V1_STR}/links/", headers=superuser_token_headers)
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)
    assert len(links) >= 2 # 可能有其他测试留下的链接 / Might have links left from other tests if scope changes
    # 检查是否包含我们刚创建的链接 / Check if it contains the links we just created
    link_ids = [l["id"] for l in links]
    assert link1["id"] in link_ids
    assert link2["id"] in link_ids

@pytest.mark.asyncio
async def test_read_link(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试读取单个链接"""
    link = await create_test_link(client, superuser_token_headers, "https://example.com/read_single", "Read Single")
    link_id = link["id"]

    response = await client.get(f"{settings.API_V1_STR}/links/{link_id}", headers=superuser_token_headers)
    assert response.status_code == 200
    read_link_data = response.json()
    assert read_link_data["id"] == link_id
    assert read_link_data["url"] == link["url"]
    assert read_link_data["name"] == link["name"]

@pytest.mark.asyncio
async def test_read_link_not_found(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试读取不存在的链接"""
    response = await client.get(f"{settings.API_V1_STR}/links/99999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_link(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试更新链接"""
    link = await create_test_link(client, superuser_token_headers, "https://example.com/update_me", "Update Me")
    link_id = link["id"]
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "tags": "updated,test",
        "is_enabled": False,
        "cookies_path": "new/path/cookies.txt"
    }
    response = await client.put(f"{settings.API_V1_STR}/links/{link_id}", json=update_data, headers=superuser_token_headers)
    assert response.status_code == 200
    updated_link = response.json()
    assert updated_link["id"] == link_id
    assert updated_link["name"] == update_data["name"]
    assert updated_link["description"] == update_data["description"]
    assert updated_link["tags"] == update_data["tags"]
    assert updated_link["is_enabled"] == update_data["is_enabled"]
    assert updated_link["cookies_path"] == update_data["cookies_path"]
    assert updated_link["updated_at"] > link["updated_at"] # 检查更新时间 / Check updated timestamp

@pytest.mark.asyncio
async def test_delete_link(client: httpx.AsyncClient, superuser_token_headers: Dict[str, str]) -> None:
    """测试删除链接"""
    link = await create_test_link(client, superuser_token_headers, "https://example.com/delete_me", "Delete Me")
    link_id = link["id"]

    # 删除链接 / Delete the link
    response_delete = await client.delete(f"{settings.API_V1_STR}/links/{link_id}", headers=superuser_token_headers)
    assert response_delete.status_code == 200
    deleted_link_data = response_delete.json()
    assert deleted_link_data["id"] == link_id

    # 尝试再次获取已删除的链接 / Try getting the deleted link again
    response_get = await client.get(f"{settings.API_V1_STR}/links/{link_id}", headers=superuser_token_headers)
    assert response_get.status_code == 404

@pytest.mark.asyncio
async def test_read_links_no_token(client: httpx.AsyncClient) -> None:
    """测试未经认证访问链接列表"""
    response = await client.get(f"{settings.API_V1_STR}/links/")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
