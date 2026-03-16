"""
任务API集成测试
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.api.server import create_app
from src.codemcp.models.base import Base
from src.codemcp.models.test import TestModel, TestStatus
from src.codemcp.models.feature import FeatureModel, FeatureStatus
from src.codemcp.models.block import BlockModel, BlockStatus
from src.codemcp.models.system import SystemModel, SystemStatus


class TestTasksAPI:
    """任务API集成测试类"""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        """设置测试数据库"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        
        # 创建测试数据
        self.system = SystemModel(
            name="测试系统",
            description="测试系统描述",
            status=SystemStatus.ACTIVE,
        )
        self.session.add(self.system)
        
        self.block = BlockModel(
            name="测试模块",
            description="测试模块描述",
            system_id=self.system.id,
            status=BlockStatus.PENDING,
        )
        self.session.add(self.block)
        
        self.feature = FeatureModel(
            name="测试功能点",
            description="测试功能点描述",
            test_command="echo 'test'",
            block_id=self.block.id,
            status=FeatureStatus.PENDING,
        )
        self.session.add(self.feature)
        
        self.session.commit()
        yield
        self.session.close()

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        app = create_app()
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    @pytest.fixture
    def sample_task_data(self):
        """示例任务数据"""
        return {
            "feature_id": self.feature.id,
            "command": "echo 'test task'",
            "max_retries": 3,
            "status": TestStatus.PENDING.value,
        }

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, client):
        """测试获取空任务列表"""
        response = await client.get("/api/v1/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_create_task(self, client, sample_task_data):
        """测试创建任务"""
        response = await client.post("/api/v1/tasks/", json=sample_task_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["feature_id"] == sample_task_data["feature_id"]
        assert data["command"] == sample_task_data["command"]
        assert data["max_retries"] == sample_task_data["max_retries"]
        assert data["status"] == sample_task_data["status"]
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_task_invalid_feature(self, client, sample_task_data):
        """测试使用无效功能点ID创建任务"""
        sample_task_data["feature_id"] = "invalid-feature-id"
        
        response = await client.post("/api/v1/tasks/", json=sample_task_data)
        
        # 应该返回错误
        assert response.status_code == 400 or response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_task(self, client, sample_task_data):
        """测试获取任务详情"""
        # 先创建任务
        create_response = await client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # 获取任务
        response = await client.get(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == task_id
        assert data["feature_id"] == sample_task_data["feature_id"]
        assert data["command"] == sample_task_data["command"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client):
        """测试获取不存在的任务"""
        response = await client.get("/api/v1/tasks/nonexistent-id")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task(self, client, sample_task_data):
        """测试更新任务"""
        # 先创建任务
        create_response = await client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # 更新任务
        update_data = {
            "command": "echo 'updated command'",
            "max_retries": 5,
            "status": TestStatus.RUNNING.value,
        }
        
        response = await client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == task_id
        assert data["command"] == update_data["command"]
        assert data["max_retries"] == update_data["max_retries"]
        assert data["status"] == update_data["status"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, client):
        """测试更新不存在的任务"""
        update_data = {
            "command": "echo 'updated command'",
        }
        
        response = await client.put("/api/v1/tasks/nonexistent-id", json=update_data)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task(self, client, sample_task_data):
        """测试删除任务"""
        # 先创建任务
        create_response = await client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # 删除任务
        response = await client.delete(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 204
        
        # 验证任务已被删除
        get_response = await client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(self, client):
        """测试删除不存在的任务"""
        response = await client.delete("/api/v1/tasks/nonexistent-id")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_task(self, client, sample_task_data):
        """测试执行任务"""
        # 先创建任务
        create_response = await client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # 执行任务
        execute_data = {
            "timeout": 30,
        }
        
        response = await client.post(f"/api/v1/tasks/{task_id}/execute", json=execute_data)
        
        # 执行可能返回202 Accepted或200 OK
        assert response.status_code in [200, 202]
        
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_next_task(self, client, sample_task_data):
        """测试获取下一个待执行任务"""
        # 先创建几个任务
        for i in range(3):
            task_data = sample_task_data.copy()
            task_data["command"] = f"echo 'task {i}'"
            await client.post("/api/v1/tasks/", json=task_data)
        
        # 获取下一个任务
        response = await client.get("/api/v1/tasks/next")
        
        # 可能返回200（有任务）或204（无任务）
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "feature_id" in data
            assert "command" in data
            assert "status" in data
        elif response.status_code == 204:
            # 无任务可用
            pass
        else:
            assert False, f"Unexpected status code: {response.status_code}"

    @pytest.mark.asyncio
    async def test_get_task_status(self, client, sample_task_data):
        """测试获取任务状态"""
        # 先创建任务
        create_response = await client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # 获取任务状态
        response = await client.get(f"/api/v1/tasks/status/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "task_id" in data
        assert "status" in data
        assert "created_at" in data
        assert data["task_id"] == task_id

    @pytest.mark.asyncio
    async def test_cancel_task(self, client, sample_task_data):
        """测试取消任务"""
        # 先创建任务
        create_response = await client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # 将任务状态设置为运行中（以便可以取消）
        update_data = {"status": TestStatus.RUNNING.value}
        await client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        # 取消任务
        response = await client.post(f"/api/v1/tasks/{task_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "task_id" in data
        assert "status" in data
        assert "cancelled" in data
        assert data["task_id"] == task_id

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(self, client, sample_task_data):
        """测试分页获取任务列表"""
        # 创建多个任务
        for i in range(15):
            task_data = sample_task_data.copy()
            task_data["command"] = f"echo 'task {i}'"
            await client.post("/api/v1/tasks/", json=task_data)
        
        # 获取第一页
        response = await client.get("/api/v1/tasks/?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] == 15
        assert len(data["items"]) == 10
        
        # 获取第二页
        response = await client.get("/api/v1/tasks/?page=2&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total"] == 15
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_tasks_with_filter(self, client, sample_task_data):
        """测试过滤获取任务列表"""
        # 创建不同状态的任务
        statuses = [TestStatus.PENDING, TestStatus.RUNNING, TestStatus.PASSED]
        
        for status in statuses:
            task_data = sample_task_data.copy()
            task_data["status"] = status.value
            task_data["command"] = f"echo 'task {status.value}'"
            await client.post("/api/v1/tasks/", json=task_data)
        
        # 过滤获取PENDING状态的任务
        response = await client.get("/api/v1/tasks/?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        
        # 应该只有PENDING状态的任务
        for item in data["items"]:
            assert item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_task_validation(self, client):
        """测试创建任务验证"""
        # 测试缺少必需字段
        invalid_data = {
            "command": "echo 'test'",
            # 缺少feature_id
        }
        
        response = await client.post("/api/v1/tasks/", json=invalid_data)
        
        assert response.status_code == 422  # 验证错误
        
        # 测试无效状态
        invalid_data = {
            "feature_id": self.feature.id,
            "command": "echo 'test'",
            "status": "invalid_status",
        }
        
        response = await client.post("/api/v1/tasks/", json=invalid_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查端点"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """测试根端点"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data