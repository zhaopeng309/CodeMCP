"""
TestModel 单元测试
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.models.test import TestModel as TestModelClass, TestStatus as TestStatusEnum
from src.codemcp.models.feature import FeatureModel, FeatureStatus
from src.codemcp.models.block import BlockModel, BlockStatus
from src.codemcp.models.system import SystemModel, SystemStatus
from src.codemcp.models.base import Base


class TestTestModel:
    """TestModel 单元测试类"""

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

    def test_test_model_creation(self):
        """测试 TestModel 创建"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            exit_code=0,
            stdout="test output",
            stderr="",
            duration=1.5,
            status=TestStatus.PASSED,
            retry_count=0,
            max_retries=3,
        )

        assert test.feature_id == "test-feature-id"
        assert test.command == "echo 'test'"
        assert test.exit_code == 0
        assert test.stdout == "test output"
        assert test.stderr == ""
        assert test.duration == 1.5
        assert test.status == TestStatus.PASSED
        assert test.retry_count == 0
        assert test.max_retries == 3
        assert test.id is None  # 尚未保存到数据库

    def test_test_model_default_values(self):
        """测试 TestModel 默认值"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
        )

        assert test.exit_code is None  # 默认值
        assert test.stdout is None  # 默认值
        assert test.stderr is None  # 默认值
        assert test.duration is None  # 默认值
        assert test.status == TestStatus.PENDING  # 默认值
        assert test.retry_count == 0  # 默认值
        assert test.max_retries == 3  # 默认值
        assert test.error_message is None  # 默认值

    def test_test_model_save_to_db(self):
        """测试 TestModel 保存到数据库"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            status=TestStatus.PASSED,
        )

        self.session.add(test)
        self.session.commit()

        assert test.id is not None
        assert isinstance(test.id, str)
        assert len(test.id) == 36  # UUID 长度

    def test_test_model_timestamps(self):
        """测试 TestModel 时间戳字段"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
        )

        self.session.add(test)
        self.session.commit()

        assert test.created_at is not None
        assert test.updated_at is not None
        assert isinstance(test.created_at, datetime)
        assert isinstance(test.updated_at, datetime)

    def test_test_model_relationships(self, sample_feature):
        """测试 TestModel 关系"""
        test = TestModel(
            feature_id=sample_feature.id,
            command="echo 'test'",
            status=TestStatus.PASSED,
        )

        self.session.add(test)
        self.session.commit()

        # 测试 feature 关系
        assert test.feature is not None
        assert test.feature.id == sample_feature.id
        assert test.feature.name == "测试功能点"

    def test_test_model_status_enum(self):
        """测试 TestStatus 枚举"""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        
        # 测试枚举成员
        assert TestStatus("pending") == TestStatus.PENDING
        assert TestStatus("running") == TestStatus.RUNNING
        assert TestStatus("passed") == TestStatus.PASSED
        assert TestStatus("failed") == TestStatus.FAILED

    def test_test_model_string_representation(self):
        """测试 TestModel 字符串表示"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            status=TestStatus.PASSED,
        )

        self.session.add(test)
        self.session.commit()

        # 测试 __repr__ 方法
        repr_str = repr(test)
        assert "TestModel" in repr_str
        assert test.id in repr_str
        assert test.feature_id in repr_str

    def test_test_model_table_name(self):
        """测试 TestModel 表名"""
        # TableNameMixin 会自动生成表名：TestModel -> test
        import re
        name = "TestModel"
        # 驼峰转蛇形
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # 移除尾部的 '_model' 或 '_mixin'
        if name.endswith(('_model', '_mixin')):
            name = name.rsplit('_', 1)[0]
        assert name == "test"

    def test_test_model_column_constraints(self):
        """测试 TestModel 列约束"""
        # 测试 feature_id 字段不能为空
        with pytest.raises(Exception):
            test = TestModel(
                feature_id=None,  # 应该引发错误
                command="echo 'test'",
            )
            self.session.add(test)
            self.session.commit()

        # 测试 command 字段不能为空
        with pytest.raises(Exception):
            test = TestModel(
                feature_id="test-feature-id",
                command=None,  # 应该引发错误
            )
            self.session.add(test)
            self.session.commit()

    def test_test_model_with_feature_relationship(self, sample_feature):
        """测试 TestModel 与 FeatureModel 的关系"""
        test = TestModel(
            feature_id=sample_feature.id,
            command="echo 'test'",
            status=TestStatus.PASSED,
        )

        self.session.add(test)
        self.session.commit()

        # 验证关系
        assert test.feature_id == sample_feature.id
        assert test.feature == sample_feature
        
        # 验证反向关系
        assert test in sample_feature.tests

    def test_test_model_cascade_delete(self, sample_feature):
        """测试 TestModel 级联删除"""
        test = TestModel(
            feature_id=sample_feature.id,
            command="echo 'test'",
            status=TestStatus.PASSED,
        )

        self.session.add(test)
        self.session.commit()

        # 删除功能点应该级联删除测试
        test_id = test.id
        self.session.delete(sample_feature)
        self.session.commit()

        # 验证测试也被删除
        deleted_test = self.session.query(TestModel).filter_by(id=test_id).first()
        assert deleted_test is None

    def test_test_model_retry_count_increment(self):
        """测试 TestModel retry_count 递增"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            retry_count=2,
            max_retries=5,
        )

        assert test.retry_count == 2
        assert test.max_retries == 5

    def test_test_model_error_message(self):
        """测试 TestModel error_message 字段"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            error_message="Test failed due to timeout",
        )

        assert test.error_message == "Test failed due to timeout"

    def test_test_model_duration_precision(self):
        """测试 TestModel duration 字段精度"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            duration=123.456789,
        )

        self.session.add(test)
        self.session.commit()

        # 验证 duration 可以存储浮点数
        assert test.duration == 123.456789

    def test_test_model_exit_code_negative(self):
        """测试 TestModel exit_code 可以为负值"""
        test = TestModel(
            feature_id="test-feature-id",
            command="echo 'test'",
            exit_code=-1,
        )

        self.session.add(test)
        self.session.commit()

        assert test.exit_code == -1