"""
队列API集成测试
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.api.server import create_app
from src.codemcp.models.base import Base
from src.codemcp.models.task_queue import TaskQueueModel, QueueStatus
from src.codemcp.models.test import TestModel, TestStatus
from src.codemcp.models.feature import FeatureModel, FeatureStatus
from src.codemcp.models.block import BlockModel, BlockStatus
from src.codemcp.models.system import SystemModel, SystemStatus


class TestQueueAPI:
    """队列API集成测试类"""

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
        
        self.test = TestModel(
            feature_id=self.feature.id,
            command="echo 'test task'",
            status=TestStatus.PENDING,
        )
        self.session.add(self.test)
        
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
    def sample_queue_data(self):
        """示例队列数据"""
        return {
            "test_id": self.test.id,
            "priority": 1,
            "status": QueueStatus.PENDING.value,
        }

    @pytest.mark.asyncio
    async def test_get_queue_empty(self, client):
        """测试获取空队列"""
        response = await client.get("/api/v1/queue/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_queue_status(self, client):
        """测试获取队列状态"""
        response = await client.get("/api/v1/queue/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_tasks" in data
        assert "pending_tasks" in data
        assert "processing_tasks" in data
        assert "completed_tasks" in data
        assert "failed_tasks" in data
        assert "cancelled_tasks" in data
        assert "queue_size" in data
        assert "window_size" in data
        assert "available_slots" in data

    @pytest.mark.asyncio
    async def test_pause_queue(self, client):
        """测试暂停队列"""
        response = await client.post("/api/v1/queue/pause")
        
        # 可能返回200或202
        assert response.status_code in [200, 202]
        
        data = response.json()
        assert "message" in data
        assert "paused" in data
        assert data["paused"] is True

    @pytest.mark.asyncio
    async def test_resume_queue(self, client):
        """测试恢复队列"""
        response = await client.post("/api/v1/queue/resume")
        
        # 可能返回200或202
        assert response.status_code in [200, 202]
        
        data = response.json()
        assert "message" in data
        assert "resumed" in data
        assert data["resumed"] is True

    @pytest.mark.asyncio
    async def test_clear_queue(self, client):
        """测试清空队列"""
        # 先添加一些任务到队列
        queue_item = TaskQueueModel(
            test_id=self.test.id,
            priority=1,
            status=QueueStatus.PENDING,
        )
        self.session.add(queue_item)
        self.session.commit()
        
        response = await client.post("/api/v1/queue/clear")
        
        # 可能返回200或202
        assert response.status_code in [200, 202]
        
        data = response.json()
        assert "message" in data
        assert "cleared" in data
        assert data["cleared"] is True
        
        # 验证队列已清空
        get_response = await client.get("/api/v1/queue/")
        assert len(get_response.json()) == 0

    @pytest.mark.asyncio
    async def test_prioritize_task(self, client):
        """测试设置任务优先级"""
        # 先创建队列项
        queue_item = TaskQueueModel(
            test_id=self.test.id,
            priority=1,
            status=QueueStatus.PENDING,
        )
        self.session.add(queue_item)
        self.session.commit()
        
        # 设置优先级
        priority_data = {
            "priority": 10,
        }
        
        response = await client.post(f"/api/v1/queue/{queue_item.id}/prioritize", json=priority_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "task_id" in data
        assert "new_priority" in data
        assert data["task_id"] == queue_item.id
        assert data["new_priority"] == 10

    @pytest.mark.asyncio
    async def test_prioritize_nonexistent_task(self, client):
        """测试设置不存在任务的优先级"""
        priority_data = {
            "priority": 10,
        }
        
        response = await client.post("/api/v1/queue/nonexistent-id/prioritize", json=priority_data)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_set_window_size(self, client):
        """测试设置窗口大小"""
        window_data = {
            "size": 10,
        }
        
        response = await client.post("/api/v1/queue/window/size", json=window_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "window_size" in data
        assert data["window_size"] == 10

    @pytest.mark.asyncio
    async def test_set_invalid_window_size(self, client):
        """测试设置无效窗口大小"""
        # 测试零大小
        window_data = {
            "size": 0,
        }
        
        response = await client.post("/api/v1/queue/window/size", json=window_data)
        
        assert response.status_code == 400
        
        # 测试负大小
        window_data = {
            "size": -1,
        }
        
        response = await client.post("/api/v1/queue/window/size", json=window_data)
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_window_status(self, client):
        """测试获取窗口状态"""
        response = await client.get("/api/v1/queue/window/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "window_size" in data
        assert "running_count" in data
        assert "waiting_count" in data
        assert "available_slots" in data
        assert "running_tasks" in data
        assert "waiting_tasks" in data

    @pytest.mark.asyncio
    async def test_queue_workflow(self, client):
        """测试完整队列工作流"""
        # 1. 获取初始状态
        status_response = await client.get("/api/v1/queue/status")
        initial_status = status_response.json()
        
        # 2. 暂停队列
        pause_response = await client.post("/api/v1/queue/pause")
        assert pause_response.status_code in [200, 202]
        
        # 3. 设置窗口大小
        window_response = await client.post("/api/v1/queue/window/size", json={"size": 5})
        assert window_response.status_code == 200
        
        # 4. 获取窗口状态
        window_status_response = await client.get("/api/v1/queue/window/status")
        window_status = window_status_response.json()
        assert window_status["window_size"] == 5
        
        # 5. 恢复队列
        resume_response = await client.post("/api/v1/queue/resume")
        assert resume_response.status_code in [200, 202]
        
        # 6. 清空队列
        clear_response = await client.post("/api/v1/queue/clear")
        assert clear_response.status_code in [200, 202]
        
        # 7. 获取最终状态
        final_status_response = await client.get("/api/v1/queue/status")
        final_status = final_status_response.json()
        
        # 验证状态变化
        assert "total_tasks" in final_status
        assert "queue_size" in final_status

    @pytest.mark.asyncio
    async def test_queue_with_multiple_tasks(self, client):
        """测试多任务队列"""
        # 创建多个测试
        tests = []
        for i in range(5):
            test = TestModel(
                feature_id=self.feature.id,
                command=f"echo 'test {i}'",
                status=TestStatus.PENDING,
            )
            self.session.add(test)
            tests.append(test)
        
        self.session.commit()
        
        # 创建多个队列项
        for i, test in enumerate(tests):
            queue_item = TaskQueueModel(
                test_id=test.id,
                priority=i,  # 不同的优先级
                status=QueueStatus.PENDING,
            )
            self.session.add(queue_item)
        
        self.session.commit()
        
        # 获取队列
        response = await client.get("/api/v1/queue/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 5
        
        # 验证队列项按优先级排序（可能）
        priorities = [item["priority"] for item in data]
        assert sorted(priorities) == priorities  # 应该按优先级升序排序

    @pytest.mark.asyncio
    async def test_queue_filter_by_status(self, client):
        """测试按状态过滤队列"""
        # 创建不同状态的队列项
        statuses = [QueueStatus.PENDING, QueueStatus.PROCESSING, QueueStatus.COMPLETED]
        
        for status in statuses:
            test = TestModel(
                feature_id=self.feature.id,
                command=f"echo 'test {status.value}'",
                status=TestStatus.PENDING,
            )
            self.session.add(test)
            self.session.flush()
            
            queue_item = TaskQueueModel(
                test_id=test.id,
                priority=1,
                status=status,
            )
            self.session.add(queue_item)
        
        self.session.commit()
        
        # 获取PENDING状态的队列项
        response = await client.get("/api/v1/queue/?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        
        # 应该只有PENDING状态的项
        for item in data:
            assert item["status"] == "pending"

    @pytest.mark.asyncio
    async def test_queue_validation(self, client):
        """测试队列验证"""
        # 测试无效优先级
        priority_data = {
            "priority": "invalid",  # 应该是数字
        }
        
        response = await client.post("/api/v1/queue/test-id/prioritize", json=priority_data)
        
        assert response.status_code == 422  # 验证错误
        
        # 测试无效窗口大小
        window_data = {
            "size": "invalid",  # 应该是数字
        }
        
        response = await client.post("/api/v1/queue/window/size", json=window_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_queue_error_handling(self, client):
        """测试队列错误处理"""
        # 测试不存在的端点
        response = await client.get("/api/v1/queue/nonexistent-endpoint")
        
        # 应该返回404
        assert response.status_code == 404
        
        # 测试无效的HTTP方法
        response = await client.put("/api/v1/queue/")
        
        # 应该返回405 Method Not Allowed
        assert response.status_code == 405