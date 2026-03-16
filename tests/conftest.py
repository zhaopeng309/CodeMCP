"""
Pytest 配置和共享 fixtures

用于测试的共享 fixtures 和配置。
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_db_session() -> AsyncGenerator[None, None]:
    """异步数据库会话 fixture

    注意: 实际项目中需要配置真实的数据库连接
    """
    # 这里返回一个空会话，实际项目需要替换为真实的数据库会话
    yield
    # 清理资源


@pytest.fixture
def sample_system_data() -> dict:
    """示例系统数据"""
    return {
        "name": "Test System",
        "description": "A test system for unit tests",
    }


@pytest.fixture
def sample_block_data() -> dict:
    """示例模块数据"""
    return {
        "name": "Test Block",
        "description": "A test block for unit tests",
        "priority": 1,
    }


@pytest.fixture
def sample_feature_data() -> dict:
    """示例功能点数据"""
    return {
        "name": "Test Feature",
        "description": "A test feature for unit tests",
        "test_command": "pytest tests/test_sample.py -xvs",
    }


@pytest.fixture
def sample_test_data() -> dict:
    """示例测试数据"""
    return {
        "command": "echo 'test'",
        "exit_code": 0,
        "stdout": "test\\n",
        "stderr": "",
        "duration": 0.1,
    }