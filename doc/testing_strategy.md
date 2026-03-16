# 单元测试与集成测试策略

## 概述
本文档详细描述 CodeMCP 项目的测试策略，包括单元测试、集成测试、端到端测试的设计和实施计划。

## 测试金字塔
```
        ┌─────────────────┐
        │  端到端测试      │ (10%)
        │  (E2E Tests)    │
        └─────────────────┘
              ┌─────────────────┐
              │  集成测试       │ (20%)
              │  (Integration)  │
              └─────────────────┘
                    ┌─────────────────┐
                    │  单元测试       │ (70%)
                    │  (Unit Tests)   │
                    └─────────────────┘
```

## 测试工具栈

### 核心测试框架
```python
# requirements-dev.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-xdist>=3.0.0  # 并行测试

# 数据库测试
pytest-postgresql>=3.0.0  # PostgreSQL 测试
pytest-sqlalchemy>=0.1.0

# API 测试
httpx>=0.25.0
starlette-testclient>=0.2.0

# 异步测试
asynctest>=0.13.0

# 代码质量
coverage>=7.0.0
mypy>=1.0.0
ruff>=0.1.0
black>=23.0.0
```

## 测试目录结构
```
tests/
├── __init__.py
├── conftest.py                    # 测试配置和固件
├── pytest.ini                     # pytest 配置
├── unit/                          # 单元测试
│   ├── test_models/              # 数据模型测试
│   │   ├── test_system.py
│   │   ├── test_block.py
│   │   ├── test_feature.py
│   │   └── test_test.py
│   ├── test_core/                # 核心逻辑测试
│   │   ├── test_state_machine.py
│   │   ├── test_task_window.py
│   │   └── test_scheduler.py
│   ├── test_utils/               # 工具函数测试
│   │   ├── test_validation.py
│   │   └── test_serialization.py
│   └── test_mcp/                 # MCP 协议测试
│       ├── test_planner_client.py
│       └── test_executor_client.py
├── integration/                   # 集成测试
│   ├── test_database/            # 数据库集成测试
│   │   ├── test_orm_integration.py
│   │   └── test_migrations.py
│   ├── test_api/                 # API 集成测试
│   │   ├── test_systems_api.py
│   │   ├── test_tasks_api.py
│   │   └── test_queue_api.py
│   └── test_cli/                 # CLI 集成测试
│       ├── test_monitor_command.py
│       └── test_queue_command.py
├── e2e/                          # 端到端测试
│   ├── test_full_workflow.py
│   └── test_failure_recovery.py
└── fixtures/                     # 测试数据
    ├── systems.json
    ├── tasks.json
    └── test_data.py
```

## 测试配置

### conftest.py
```python
# tests/conftest.py
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.codemcp.database.session import SessionLocal, get_db
from src.codemcp.models.base import Base
from src.codemcp.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """测试配置"""
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        DEBUG=True,
        TESTING=True,
    )


@pytest.fixture(scope="session")
def engine(test_settings):
    """测试数据库引擎"""
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    return engine


@pytest.fixture(scope="session")
def create_tables(engine):
    """创建测试表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, create_tables) -> Generator[Session, None, None]:
    """数据库会话固件"""
    connection = engine.connect()
    transaction = connection.begin()
    
    SessionLocal.configure(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI 测试客户端"""
    from fastapi.testclient import TestClient
    from src.codemcp.api.server import app
    
    # 覆盖依赖
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_system(db_session):
    """示例系统"""
    from src.codemcp.models.system import System
    
    system = System(
        name="测试系统",
        description="用于测试的系统",
        status="active",
    )
    db_session.add(system)
    db_session.commit()
    db_session.refresh(system)
    
    return system


@pytest.fixture
def sample_block(db_session, sample_system):
    """示例模块"""
    from src.codemcp.models.block import Block
    
    block = Block(
        system_id=sample_system.id,
        name="测试模块",
        description="用于测试的模块",
        priority=0,
        status="pending",
    )
    db_session.add(block)
    db_session.commit()
    db_session.refresh(block)
    
    return block


@pytest.fixture
def sample_feature(db_session, sample_block):
    """示例功能点"""
    from src.codemcp.models.feature import Feature
    
    feature = Feature(
        block_id=sample_block.id,
        name="测试功能",
        description="用于测试的功能点",
        test_command="echo 'test'",
        priority=0,
        status="pending",
    )
    db_session.add(feature)
    db_session.commit()
    db_session.refresh(feature)
    
    return feature


@pytest_asyncio.fixture
async def async_client():
    """异步 HTTP 客户端"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        yield client
```

## 单元测试示例

### 数据模型测试
```python
# tests/unit/test_models/test_system.py
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.codemcp.models.system import System


class TestSystemModel:
    """System 模型测试"""
    
    def test_create_system(self, db_session):
        """测试创建系统"""
        system = System(
            name="测试系统",
            description="测试描述",
            status="active",
        )
        
        db_session.add(system)
        db_session.commit()
        
        assert system.id is not None
        assert system.name == "测试系统"
        assert system.status == "active"
        assert isinstance(system.created_at, datetime)
        assert isinstance(system.updated_at, datetime)
    
    def test_system_name_unique(self, db_session, sample_system):
        """测试系统名称唯一性约束"""
        duplicate_system = System(
            name=sample_system.name,  # 重复名称
            description="另一个系统",
            status="active",
        )
        
        db_session.add(duplicate_system)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
    
    def test_system_stats_property(self, db_session, sample_system):
        """测试系统统计属性"""
        stats = sample_system.stats
        
        assert isinstance(stats, dict)
        assert "total_blocks" in stats
        assert "completed_blocks" in stats
        assert "total_features" in stats
        assert "completed_features" in stats
    
    def test_system_repr(self, sample_system):
        """测试字符串表示"""
        repr_str = repr(sample_system)
        
        assert "System" in repr_str
        assert str(sample_system.id) in repr_str
        assert sample_system.name in repr_str
        assert sample_system.status in repr_str
```

### 状态机测试
```python
# tests/unit/test_core/test_state_machine.py
import pytest
from unittest.mock import Mock, AsyncMock

from src.codemcp.core.feature_state_machine import FeatureStateMachine
from src.codemcp.models.feature import Feature


class TestFeatureStateMachine:
    """Feature 状态机测试"""
    
    @pytest.fixture
    def feature(self):
        """测试用 Feature"""
        return Feature(
            id=1,
            name="测试功能",
            test_command="echo test",
            retry_count=0,
            max_retries=3,
        )
    
    def test_initial_state(self, feature):
        """测试初始状态"""
        fsm = FeatureStateMachine(feature)
        
        assert fsm.current_state == "pending"
        assert len(fsm.transitions) > 0
    
    def test_valid_transition(self, feature):
        """测试有效状态转移"""
        fsm = FeatureStateMachine(feature)
        
        # pending -> running
        context = {"executor_id": "test-executor"}
        result = fsm.transition("running", context)
        
        assert result is True
        assert fsm.current_state == "running"
        assert feature.status == "running"
        assert feature.started_at is not None
    
    def test_invalid_transition(self, feature):
        """测试无效状态转移"""
        fsm = FeatureStateMachine(feature)
        
        # pending -> passed (无效转移)
        result = fsm.transition("passed", {})
        
        assert result is False
        assert fsm.current_state == "pending"
        assert feature.status == "pending"
    
    def test_failure_with_retry(self, feature):
        """测试失败重试"""
        fsm = FeatureStateMachine(feature)
        
        # pending -> running
        fsm.transition("running", {"executor_id": "test"})
        
        # running -> failed
        context = {
            "exit_code": 1,
            "duration": 10.0,
            "error_details": "测试错误",
        }
        fsm.transition("failed", context)
        
        assert fsm.current_state == "failed"
        assert feature.retry_count == 1
        
        # failed -> pending (重试)
        result = fsm.transition("pending", {})
        
        assert result is True
        assert fsm.current_state == "pending"
        assert feature.retry_count == 1  # 重试次数不变
        assert feature.started_at is None
    
    def test_failure_with_abort(self, feature):
        """测试失败中止"""
        feature.retry_count = 3  # 达到最大重试次数
        
        fsm = FeatureStateMachine(feature)
        fsm.current_state = "failed"
        
        # failed -> aborted
        result = fsm.transition("aborted", {})
        
        assert result is True
        assert fsm.current_state == "aborted"
        assert feature.status == "aborted"
```

### 任务窗口测试
```python
# tests/unit/test_core/test_task_window.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.codemcp.core.task_window import WindowManager, WindowConfig
from src.codemcp.models.feature import Feature


class TestWindowManager:
    """窗口管理器测试"""
    
    @pytest.fixture
    def window_manager(self, db_session):
        """窗口管理器固件"""
        config = WindowConfig(size=3)  # 小窗口便于测试
        return WindowManager(db_session, config)
    
    @pytest.mark.asyncio
    async def test_add_task(self, window_manager, sample_feature):
        """测试添加任务"""
        result = await window_manager.add_task(sample_feature)
        
        assert result is True
        
        # 检查队列状态
        status = await window_manager.get_queue_status()
        assert status["queue_size"] == 1
    
    @pytest.mark.asyncio
    async def test_reserve_slot(self, window_manager, sample_feature):
        """测试预留槽位"""
        # 先添加任务
        await window_manager.add_task(sample_feature)
        
        # 预留槽位
        slot_id = await window_manager.reserve_slot(
            sample_feature,
            executor_id="test-executor"
        )
        
        assert slot_id is not None
        assert 1 <= slot_id <= 3
        
        # 检查槽位状态
        slots = await window_manager.get_available_slots()
        slot = next(s for s in slots if s["slot_id"] == slot_id)
        
        assert slot["status"] == "reserved"
        assert slot["feature_id"] == sample_feature.id
        assert slot["executor_id"] == "test-executor"
    
    @pytest.mark.asyncio
    async def test_window_full(self, window_manager, db_session):
        """测试窗口满的情况"""
        # 创建多个任务填满窗口
        features = []
        for i in range(5):
            feature = Feature(
                block_id=1,
                name=f"测试功能{i}",
                test_command=f"echo test{i}",
                priority=i,
            )
            db_session.add(feature)
            features.append(feature)
        
        db_session.commit()
        
        # 添加所有任务
        for feature in features:
            await window_manager.add_task(feature)
        
        # 检查队列状态
        status = await window_manager.get_queue_status()
        assert status["queue_size"] == 5
        assert status["window_used"] == 0  # 尚未预留
    
    @pytest.mark.asyncio
    async def test_complete_execution(self, window_manager, sample_feature):
        """测试完成任务执行"""
        # 添加并预留任务
        await window_manager.add_task(sample_feature)
        slot_id = await window_manager.reserve_slot(
            sample_feature,
            executor_id="test-executor"
        )
        
        # 开始执行
        await window_manager.start_execution(slot_id)
        
        # 完成任务
        result = await window_manager.complete_execution(
            slot_id=slot_id,
            success=True,
            exit_code=0,
            stdout="测试通过",
            duration=5.0,
        )
        
        assert result is True
        
        # 检查统计
        status = await window_manager.get_queue_status()
        assert status["stats"]["total_processed"] == 1
        assert status["stats"]["successful"] == 1
```

## 集成测试示例

### API 集成测试
```python
# tests/integration/test_api/test_systems_api.py
import pytest
from fastapi import status


class TestSystemsAPI:
    """系统 API 集成测试"""
    
    def test_create_system(self, client):
        """测试创建系统"""
        response = client.post(
            "/api/v1/systems",
            json={
                "name": "集成测试系统",
                "description": "用于集成测试",
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["name"] == "集成测试系统"
    
    def test_list_systems(self, client, sample_system):
        """测试列出系统"""
        response = client.get("/api/v1/systems")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "systems" in data["data"]
        assert len(data["data"]["systems"]) >= 1
    
    def test_get_system(self, client, sample_system):
        """测试获取系统详情"""
        response = client.get(f"/api/v1/systems/{sample_system.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == sample_system.id
        assert data["data"]["name"] == sample_system.name
    
    def test_update_system(self, client, sample_system):
        """测试更新系统"""
        response = client.put(
            f"/api/v1/systems/{sample_system.id}",
            json={
                "name": "更新后的系统",
                "description": "更新描述",
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["name"] == "更新后的系统"
```

### 数据库集成测试
```python
# tests/integration/test_database/test_orm_integration.py
import pytest
from sqlalchemy import select

from src.codemcp.models.system import System
from src.codemcp.models.block import Block
from src.codemcp.models.feature import Feature


class TestORMIntegration:
    """ORM 集成测试"""
    
    def test_cascade_delete(self, db_session, sample_system):
        """测试级联删除"""
        # 创建关联数据
        block = Block(
            system_id=sample_system.id,
            name="测试模块",
            description="测试模块描述",
            priority=0,
            status="pending",
        )
        db_session.add(block)
        db_session.commit()
        
        feature = Feature(
            block_id=block.id,
            name="测试功能",
            description="测试功能描述",
            test_command="echo test",
            priority=0,
            status="pending",
        )
        db_session.add(feature)
        db_session.commit()
        
        # 删除系统，应该级联删除关联的模块和功能点
        db_session.delete(sample_system)
        db_session.commit()
        
        # 验证关联数据已被删除
        remaining_blocks = db_session.execute(
            select(Block).where(Block.system_id == sample_system.id)
        ).scalars().all()
        
        remaining_features = db_session.execute(
            select(Feature).where(Feature.block_id == block.id)
        ).scalars().all()
        
        assert len(remaining_blocks) == 0
        assert len(remaining_features) == 0
    
    def test_relationship_integrity(self, db_session, sample_system):
        """测试关系完整性"""
        # 创建完整的层次结构
        block = Block(
            system_id=sample_system.id,
            name="父模块",
            priority=0,
            status="pending",
        )
        db_session.add(block)
        db_session.commit()
        
        feature = Feature(
            block_id=block.id,
            name="子功能",
            test_command="pytest test.py",
            priority=0,
            status="pending",
        )
        db_session.add(feature)
        db_session.commit()
        
        # 验证关系
        assert feature.block.id == block.id
        assert block.system.id == sample_system.id
        assert feature in block.features
        assert block in sample_system.blocks

## 端到端测试示例

### 完整工作流测试
```python
# tests/e2e/test_full_workflow.py
import pytest
import asyncio
from datetime import datetime

from src.codemcp.core.task_scheduler import TaskScheduler
from src.codemcp.core.task_window import WindowManager


class TestFullWorkflow:
    """完整工作流端到端测试"""
    
    @pytest.mark.asyncio
    async def test_plan_to_completion(self, db_session):
        """测试从计划创建到任务完成的完整流程"""
        # 1. 创建测试数据
        from src.codemcp.models import System, Block, Feature
        
        system = System(name="E2E测试系统", status="active")
        db_session.add(system)
        db_session.commit()
        
        block = Block(
            system_id=system.id,
            name="E2E测试模块",
            priority=0,
            status="pending",
        )
        db_session.add(block)
        db_session.commit()
        
        feature = Feature(
            block_id=block.id,
            name="E2E测试功能",
            test_command="echo '测试通过'",
            priority=0,
            status="pending",
        )
        db_session.add(feature)
        db_session.commit()
        
        # 2. 初始化调度器和窗口管理器
        window_manager = WindowManager(db_session)
        await window_manager.start()
        
        scheduler = TaskScheduler(db_session)
        await scheduler.start()
        
        try:
            # 3. 添加任务到队列
            await window_manager.add_task(feature)
            
            # 4. 模拟Executor获取任务
            slot_id = await window_manager.reserve_slot(
                feature,
                executor_id="e2e-executor"
            )
            assert slot_id is not None
            
            # 5. 开始执行
            await window_manager.start_execution(slot_id)
            assert feature.status == "running"
            
            # 6. 完成任务
            await window_manager.complete_execution(
                slot_id=slot_id,
                success=True,
                exit_code=0,
                stdout="测试通过",
                duration=10.0,
            )
            
            # 7. 验证结果
            assert feature.status == "passed"
            assert block.status == "completed"
            assert len(feature.tests) == 1
            assert feature.tests[0].exit_code == 0
            
            # 8. 验证统计信息
            status = await window_manager.get_queue_status()
            assert status["stats"]["total_processed"] == 1
            assert status["stats"]["successful"] == 1
            
        finally:
            # 清理
            await window_manager.stop()
            await scheduler.stop()

## 测试运行和报告

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定类型的测试
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# 运行带覆盖率的测试
pytest --cov=src/codemcp --cov-report=html

# 并行运行测试
pytest -n auto

# 运行特定测试文件
pytest tests/unit/test_models/test_system.py -v
```

### 测试报告
```bash
# 生成HTML报告
pytest --html=report.html --self-contained-html

# 生成JUnit XML报告（用于CI/CD）
pytest --junitxml=report.xml

# 生成覆盖率报告
coverage html
```

### 持续集成配置
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: codemcp_test
          POSTGRES_USER: codemcp
          POSTGRES_PASSWORD: codemcp
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://codemcp:codemcp@localhost/codemcp_test
      run: |
        pytest --cov=src/codemcp --cov-report=xml --junitxml=report.xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          report.xml
          coverage.xml
```

## 测试最佳实践

### 1. 测试命名规范
- 测试类名: `Test{ClassName}`
- 测试方法名: `test_{scenario}_{expected_result}`
- 使用描述性的测试名称

### 2. 测试结构
- 每个测试方法只测试一个场景
- 使用Arrange-Act-Assert模式
- 避免测试间的依赖

### 3. 测试数据管理
- 使用fixture创建测试数据
- 测试后清理数据
- 使用工厂函数生成复杂数据

### 4. 异步测试
- 使用`pytest.mark.asyncio`装饰器
- 正确处理异步上下文
- 避免阻塞操作

### 5. 数据库测试
- 使用内存数据库或测试数据库
- 每个测试使用独立的事务
- 测试后回滚更改

## 性能测试

### 负载测试
```python
# tests/performance/test_load.py
import pytest
import asyncio
from datetime import datetime

from src.codemcp.core.task_window import WindowManager


class TestLoadPerformance:
    """负载性能测试"""
    
    @pytest.mark.asyncio
    async def test_window_manager_performance(self, db_session):
        """测试窗口管理器性能"""
        window_manager = WindowManager(db_session)
        
        # 创建大量任务
        tasks = []
        for i in range(1000):
            from src.codemcp.models.feature import Feature
            feature = Feature(
                block_id=1,
                name=f"性能测试任务{i}",
                test_command=f"echo test{i}",
                priority=i % 10,
            )
            tasks.append(feature)
        
        # 批量添加任务并测量时间
        start_time = datetime.now()
        
        for feature in tasks:
            await window_manager.add_task(feature)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 性能要求：1000个任务添加时间 < 5秒
        assert duration < 5.0
        
        # 验证队列状态
        status = await window_manager.get_queue_status()
        assert status["queue_size"] == 1000
```

## 安全测试

### 认证和授权测试
```python
# tests/security/test_auth.py
import pytest
from fastapi import status


class TestAuthentication:
    """认证测试"""
    
    def test_unauthenticated_access(self, client):
        """测试未认证访问"""
        response = client.get("/api/v1/systems")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_api_key(self, client):
        """测试无效API密钥"""
        response = client.get(
            "/api/v1/systems",
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_role_based_access(self, client_with_planner, client_with_executor):
        """测试基于角色的访问控制"""
        # Planner可以创建系统
        response = client_with_planner.post(
            "/api/v1/systems",
            json={"name": "测试系统"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Executor不能创建系统
        response = client_with_executor.post(
            "/api/v1/systems",
            json={"name": "测试系统"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
```

## 总结

本文档提供了CodeMCP项目的完整测试策略，包括：

1. **测试金字塔结构**: 单元测试(70%)、集成测试(20%)、端到端测试(10%)
2. **完整的测试工具栈**: pytest、coverage、mypy等
3. **详细的测试示例**: 模型测试、状态机测试、API测试等
4. **持续集成配置**: GitHub Actions工作流
5. **性能和安全测试**: 负载测试和认证测试

通过实施这个测试策略，可以确保CodeMCP项目的代码质量、功能正确性和系统可靠性。