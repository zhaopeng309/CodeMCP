"""
FeatureModel 单元测试
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.models.feature import FeatureModel, FeatureStatus
from src.codemcp.models.block import BlockModel, BlockStatus
from src.codemcp.models.system import SystemModel, SystemStatus
from src.codemcp.models.base import Base


class TestFeatureModel:
    """FeatureModel 单元测试类"""

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

    def test_feature_model_creation(self):
        """测试 FeatureModel 创建"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            status=FeatureStatus.PENDING,
        )

        assert feature.name == "测试功能点"
        assert feature.description == "这是一个测试功能点"
        assert feature.test_command == "pytest tests/test_sample.py -xvs"
        assert feature.status == FeatureStatus.PENDING
        assert feature.id is None  # 尚未保存到数据库

    def test_feature_model_default_values(self):
        """测试 FeatureModel 默认值"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
        )

        assert feature.status == FeatureStatus.PENDING  # 默认值

    def test_feature_model_save_to_db(self):
        """测试 FeatureModel 保存到数据库"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            status=FeatureStatus.PENDING,
        )

        self.session.add(feature)
        self.session.commit()

        assert feature.id is not None
        assert isinstance(feature.id, str)
        assert len(feature.id) == 36  # UUID 长度

    def test_feature_model_timestamps(self):
        """测试 FeatureModel 时间戳字段"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
        )

        self.session.add(feature)
        self.session.commit()

        assert feature.created_at is not None
        assert feature.updated_at is not None
        assert isinstance(feature.created_at, datetime)
        assert isinstance(feature.updated_at, datetime)

    def test_feature_model_relationships(self, sample_block):
        """测试 FeatureModel 关系"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            block_id=sample_block.id,
        )

        self.session.add(feature)
        self.session.commit()

        # 测试 block 关系
        assert feature.block is not None
        assert feature.block.id == sample_block.id
        assert feature.block.name == "测试模块"

        # 测试 tests 关系
        assert feature.tests == []  # 初始为空列表

    def test_feature_model_status_enum(self):
        """测试 FeatureStatus 枚举"""
        assert FeatureStatus.PENDING.value == "pending"
        assert FeatureStatus.RUNNING.value == "running"
        assert FeatureStatus.PASSED.value == "passed"
        assert FeatureStatus.FAILED.value == "failed"
        assert FeatureStatus.ABORTED.value == "aborted"
        
        # 测试枚举成员
        assert FeatureStatus("pending") == FeatureStatus.PENDING
        assert FeatureStatus("running") == FeatureStatus.RUNNING
        assert FeatureStatus("passed") == FeatureStatus.PASSED
        assert FeatureStatus("failed") == FeatureStatus.FAILED
        assert FeatureStatus("aborted") == FeatureStatus.ABORTED

    def test_feature_model_string_representation(self):
        """测试 FeatureModel 字符串表示"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
        )

        self.session.add(feature)
        self.session.commit()

        # 测试 __repr__ 方法
        repr_str = repr(feature)
        assert "FeatureModel" in repr_str
        assert feature.id in repr_str
        assert "测试功能点" in repr_str

    def test_feature_model_table_name(self):
        """测试 FeatureModel 表名"""
        # TableNameMixin 会自动生成表名：FeatureModel -> feature
        import re
        name = "FeatureModel"
        # 驼峰转蛇形
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # 移除尾部的 '_model' 或 '_mixin'
        if name.endswith(('_model', '_mixin')):
            name = name.rsplit('_', 1)[0]
        assert name == "feature"

    def test_feature_model_column_constraints(self):
        """测试 FeatureModel 列约束"""
        # 测试 name 字段不能为空
        with pytest.raises(Exception):
            feature = FeatureModel(
                name=None,  # 应该引发错误
                description="这是一个测试功能点",
                test_command="pytest tests/test_sample.py -xvs",
            )
            self.session.add(feature)
            self.session.commit()

        # 测试 test_command 字段不能为空
        with pytest.raises(Exception):
            feature = FeatureModel(
                name="测试功能点",
                description="这是一个测试功能点",
                test_command=None,  # 应该引发错误
            )
            self.session.add(feature)
            self.session.commit()

    def test_feature_model_with_block_relationship(self, sample_block):
        """测试 FeatureModel 与 BlockModel 的关系"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            block_id=sample_block.id,
        )

        self.session.add(feature)
        self.session.commit()

        # 验证关系
        assert feature.block_id == sample_block.id
        assert feature.block == sample_block
        
        # 验证反向关系
        assert feature in sample_block.features

    def test_feature_model_cascade_delete(self, sample_block):
        """测试 FeatureModel 级联删除"""
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            block_id=sample_block.id,
        )

        self.session.add(feature)
        self.session.commit()

        # 删除模块应该级联删除功能点
        feature_id = feature.id
        self.session.delete(sample_block)
        self.session.commit()

        # 验证功能点也被删除
        deleted_feature = self.session.query(FeatureModel).filter_by(id=feature_id).first()
        assert deleted_feature is None

    def test_feature_model_test_command_length(self):
        """测试 FeatureModel test_command 字段长度"""
        # 测试长命令
        long_command = "pytest " + "tests/" * 100 + "test_sample.py -xvs"
        feature = FeatureModel(
            name="测试功能点",
            description="这是一个测试功能点",
            test_command=long_command,
        )

        self.session.add(feature)
        self.session.commit()

        assert feature.test_command == long_command

    def test_feature_model_optional_description(self):
        """测试 FeatureModel description 字段可选"""
        feature = FeatureModel(
            name="测试功能点",
            test_command="pytest tests/test_sample.py -xvs",
            description=None,  # 应该允许为空
        )

        self.session.add(feature)
        self.session.commit()

        assert feature.description is None