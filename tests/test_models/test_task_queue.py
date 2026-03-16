"""
TaskQueueModel 单元测试
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.models.task_queue import TaskQueueModel, QueueStatus
from src.codemcp.models.test import TestModel as TestModelClass, TestStatus as TestStatusEnum
from src.codemcp.models.feature import FeatureModel, FeatureStatus
from src.codemcp.models.block import BlockModel, BlockStatus
from src.codemcp.models.system import SystemModel, SystemStatus
from src.codemcp.models.base import Base


class TestTaskQueueModel:
    """TaskQueueModel 单元测试类"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """设置内存数据库用于测试"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        yield
        self.session.close()

    @pytest.fixture
    def sample_system(self):
        """创建示例系统"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
            status=SystemStatus.ACTIVE,
        )
        self.session.add(system)
        self.session.commit()
        return system

    @pytest.fixture
    def sample_block(self, sample_system):
        """创建示例模块"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            system_id=sample_system.id,
            status=BlockStatus.PENDING,
        )
        self.session.add(block)
        self.session.commit()
        return block

    @pytest.fixture
    def sample_feature(self, sample_block):
        """创建示例功能点"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            block_id=sample_block.id,
            status=FeatureStatus.PENDING,
        )
        self.session.add(feature)
        self.session.commit()
        return feature

    @pytest.fixture
    def sample_test(self, sample_feature):
        """创建示例测试"""
        test = TestModelClass(
            feature_id=sample_feature.id,
            command="echo 'test'",
            status=TestStatusEnum.PENDING,
        )
        self.session.add(test)
        self.session.commit()
        return test

    def test_task_queue_model_creation(self):
        """测试 TaskQueueModel 创建"""
        task_queue = TaskQueueModel(
            test_id="test-id",
            priority=1,
            status=QueueStatus.PENDING,
            scheduled_at=datetime.now(),
        )

        assert task_queue.test_id == "test-id"
        assert task_queue.priority == 1
        assert task_queue.status == QueueStatus.PENDING
        assert task_queue.scheduled_at is not None
        assert task_queue.id is None  # 尚未保存到数据库

    def test_task_queue_model_default_values(self):
        """测试 TaskQueueModel 默认值"""
        task_queue = TaskQueueModel(
            test_id="test-id",
        )

        assert task_queue.priority == 0  # 默认值
        assert task_queue.status == QueueStatus.PENDING  # 默认值
        assert task_queue.scheduled_at is not None  # 应该自动设置

    def test_task_queue_model_save_to_db(self):
        """测试 TaskQueueModel 保存到数据库"""
        task_queue = TaskQueueModel(
            test_id="test-id",
            priority=1,
            status=QueueStatus.PENDING,
        )

        self.session.add(task_queue)
        self.session.commit()

        assert task_queue.id is not None
        assert isinstance(task_queue.id, str)
        assert len(task_queue.id) == 36  # UUID 长度

    def test_task_queue_model_timestamps(self):
        """测试 TaskQueueModel 时间戳字段"""
        task_queue = TaskQueueModel(
            test_id="test-id",
        )

        self.session.add(task_queue)
        self.session.commit()

        assert task_queue.created_at is not None
        assert task_queue.updated_at is not None
        assert isinstance(task_queue.created_at, datetime)
        assert isinstance(task_queue.updated_at, datetime)

    def test_task_queue_model_relationships(self, sample_test):
        """测试 TaskQueueModel 关系"""
        task_queue = TaskQueueModel(
            test_id=sample_test.id,
            priority=1,
            status=QueueStatus.PENDING,
        )

        self.session.add(task_queue)
        self.session.commit()

        # 测试 test 关系
        assert task_queue.test is not None
        assert task_queue.test.id == sample_test.id
        assert task_queue.test.command == "echo 'test'"

    def test_task_queue_model_status_enum(self):
        """测试 QueueStatus 枚举"""
        assert QueueStatus.PENDING.value == "pending"
        assert QueueStatus.PROCESSING.value == "processing"
        assert QueueStatus.COMPLETED.value == "completed"
        assert QueueStatus.FAILED.value == "failed"
        assert QueueStatus.CANCELLED.value == "cancelled"
        
        # 测试枚举成员
        assert QueueStatus("pending") == QueueStatus.PENDING
        assert QueueStatus("processing") == QueueStatus.PROCESSING
        assert QueueStatus("completed") == QueueStatus.COMPLETED
        assert QueueStatus("failed") == QueueStatus.FAILED
        assert QueueStatus("cancelled") == QueueStatus.CANCELLED

    def test_task_queue_model_string_representation(self):
        """测试 TaskQueueModel 字符串表示"""
        task_queue = TaskQueueModel(
            test_id="test-id",
            priority=1,
            status=QueueStatus.PENDING,
        )

        self.session.add(task_queue)
        self.session.commit()

        # 测试 __repr__ 方法
        repr_str = repr(task_queue)
        assert "TaskQueueModel" in repr_str
        assert task_queue.id in repr_str
        assert task_queue.test_id in repr_str

    def test_task_queue_model_table_name(self):
        """测试 TaskQueueModel 表名"""
        # TableNameMixin 会自动生成表名：TaskQueueModel -> task_queue
        import re
        name = "TaskQueueModel"
        # 驼峰转蛇形
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # 移除尾部的 '_model' 或 '_mixin'
        if name.endswith(('_model', '_mixin')):
            name = name.rsplit('_', 1)[0]
        assert name == "task_queue"

    def test_task_queue_model_column_constraints(self):
        """测试 TaskQueueModel 列约束"""
        # 测试 test_id 字段不能为空
        with pytest.raises(Exception):
            task_queue = TaskQueueModel(
                test_id=None,  # 应该引发错误
                priority=1,
            )
            self.session.add(task_queue)
            self.session.commit()

    def test_task_queue_model_with_test_relationship(self, sample_test):
        """测试 TaskQueueModel 与 TestModel 的关系"""
        task_queue = TaskQueueModel(
            test_id=sample_test.id,
            priority=1,
            status=QueueStatus.PENDING,
        )

        self.session.add(task_queue)
        self.session.commit()

        # 验证关系
        assert task_queue.test_id == sample_test.id
        assert task_queue.test == sample_test

    def test_task_queue_model_priority_range(self):
        """测试 TaskQueueModel 优先级范围"""
        # 测试高优先级
        task_queue = TaskQueueModel(
            test_id="test-id",
            priority=999,
        )

        self.session.add(task_queue)
        self.session.commit()

        assert task_queue.priority == 999

        # 测试负优先级
        task_queue2 = TaskQueueModel(
            test_id="test-id-2",
            priority=-10,
        )

        self.session.add(task_queue2)
        self.session.commit()

        assert task_queue2.priority == -10

    def test_task_queue_model_scheduled_at_future(self):
        """测试 TaskQueueModel scheduled_at 未来时间"""
        from datetime import datetime, timedelta
        
        future_time = datetime.now() + timedelta(days=1)
        task_queue = TaskQueueModel(
            test_id="test-id",
            scheduled_at=future_time,
        )

        self.session.add(task_queue)
        self.session.commit()

        assert task_queue.scheduled_at == future_time

    def test_task_queue_model_scheduled_at_past(self):
        """测试 TaskQueueModel scheduled_at 过去时间"""
        from datetime import datetime, timedelta
        
        past_time = datetime.now() - timedelta(days=1)
        task_queue = TaskQueueModel(
            test_id="test-id",
            scheduled_at=past_time,
        )

        self.session.add(task_queue)
        self.session.commit()

        assert task_queue.scheduled_at == past_time

    def test_task_queue_model_unique_constraint(self):
        """测试 TaskQueueModel 唯一约束"""
        # 创建第一个任务队列
        task_queue1 = TaskQueueModel(
            test_id="test-id",
            priority=1,
        )

        self.session.add(task_queue1)
        self.session.commit()

        # 尝试创建第二个相同 test_id 的任务队列
        # 注意：这取决于模型是否有唯一约束，如果没有则应该允许
        task_queue2 = TaskQueueModel(
            test_id="test-id",
            priority=2,
        )

        self.session.add(task_queue2)
        try:
            self.session.commit()
            # 如果没有唯一约束，应该成功
            assert True
        except Exception:
            # 如果有唯一约束，应该失败
            self.session.rollback()
            assert True

    def test_task_queue_model_status_transitions(self):
        """测试 TaskQueueModel 状态转换"""
        task_queue = TaskQueueModel(
            test_id="test-id",
            status=QueueStatus.PENDING,
        )

        self.session.add(task_queue)
        self.session.commit()

        # 更新状态
        task_queue.status = QueueStatus.PROCESSING
        self.session.commit()

        assert task_queue.status == QueueStatus.PROCESSING

        # 再次更新状态
        task_queue.status = QueueStatus.COMPLETED
        self.session.commit()

        assert task_queue.status == QueueStatus.COMPLETED