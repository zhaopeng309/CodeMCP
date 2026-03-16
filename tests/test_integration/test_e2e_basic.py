"""
端到端集成测试

测试CodeMCP系统的核心功能流程。
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text

from codemcp.config import settings
from codemcp.database.engine import engine
from codemcp.models.system import SystemModel
from codemcp.models.block import BlockModel
from codemcp.models.feature import FeatureModel
from codemcp.models.test import TestModel
from codemcp.models.task_queue import TaskQueueModel, QueueStatus


@pytest.mark.asyncio
async def test_database_connection():
    """测试数据库连接"""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("✓ 数据库连接测试通过")


@pytest.mark.asyncio
async def test_system_creation():
    """测试系统创建流程"""
    # 创建异步会话
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # 创建系统
        system = SystemModel(
            name="测试系统",
            description="用于集成测试的系统",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(system)
        await session.commit()
        await session.refresh(system)
        
        assert system.id is not None
        assert system.name == "测试系统"
        print(f"✓ 系统创建测试通过 - 系统ID: {system.id}")
        
        # 创建模块
        block = BlockModel(
            system_id=system.id,
            name="测试模块",
            description="测试系统的模块",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(block)
        await session.commit()
        await session.refresh(block)
        
        assert block.id is not None
        assert block.system_id == system.id
        print(f"✓ 模块创建测试通过 - 模块ID: {block.id}")
        
        # 创建功能点
        feature = FeatureModel(
            block_id=block.id,
            name="测试功能",
            description="测试功能点",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(feature)
        await session.commit()
        await session.refresh(feature)
        
        assert feature.id is not None
        assert feature.block_id == block.id
        print(f"✓ 功能点创建测试通过 - 功能点ID: {feature.id}")
        
        # 创建测试
        test = TestModel(
            feature_id=feature.id,
            name="集成测试",
            description="端到端集成测试",
            command="pytest tests/test_integration/ -v",
            expected_output="所有测试通过",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(test)
        await session.commit()
        await session.refresh(test)
        
        assert test.id is not None
        assert test.feature_id == feature.id
        print(f"✓ 测试创建测试通过 - 测试ID: {test.id}")
        
        # 创建任务
        task = TaskQueueModel(
            test_id=test.id,
            system_id=system.id,
            block_id=block.id,
            feature_id=feature.id,
            command=test.command,
            priority=1,
            status=QueueStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        
        assert task.id is not None
        assert task.test_id == test.id
        print(f"✓ 任务创建测试通过 - 任务ID: {task.id}")
        
        # 清理测试数据
        await session.delete(task)
        await session.delete(test)
        await session.delete(feature)
        await session.delete(block)
        await session.delete(system)
        await session.commit()
        
        print("✓ 数据清理完成")


@pytest.mark.asyncio
async def test_config_loading():
    """测试配置加载"""
    assert settings is not None
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'host')
    assert hasattr(settings, 'port')
    print("✓ 配置加载测试通过")


@pytest.mark.asyncio
async def test_api_status_endpoint():
    """测试API状态端点（模拟）"""
    # 这里模拟API调用，实际项目中应该使用TestClient
    from codemcp.api.routes.status import get_system_status
    from unittest.mock import AsyncMock, MagicMock
    
    # 创建模拟的数据库会话
    mock_db = AsyncMock(spec=AsyncSession)
    mock_settings = MagicMock()
    
    # 模拟数据库查询
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5  # 模拟有5个任务
    
    async def mock_execute(query):
        return mock_result
    
    mock_db.execute = mock_execute
    
    # 调用状态端点
    status_result = await get_system_status(db=mock_db, _settings=mock_settings)
    
    assert status_result is not None
    assert 'status' in status_result
    assert 'statistics' in status_result
    print("✓ API状态端点测试通过")


def test_integration_workflow():
    """集成测试工作流"""
    print("\n" + "="*60)
    print("CodeMCP 端到端集成测试")
    print("="*60)
    
    # 运行异步测试
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(test_database_connection())
        loop.run_until_complete(test_system_creation())
        loop.run_until_complete(test_config_loading())
        loop.run_until_complete(test_api_status_endpoint())
        
        print("\n" + "="*60)
        print("所有集成测试通过！ ✓")
        print("="*60)
    finally:
        loop.close()


if __name__ == "__main__":
    """直接运行集成测试"""
    test_integration_workflow()