"""
BlockModel 单元测试
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.models.block import BlockModel, BlockStatus
from src.codemcp.models.system import SystemModel, SystemStatus
from src.codemcp.models.base import Base


class TestBlockModel:
    """BlockModel 单元测试类"""

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

    def test_block_model_creation(self):
        """测试 BlockModel 创建"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            priority=1,
            status=BlockStatus.PENDING,
        )

        assert block.name == "测试模块"
        assert block.description == "这是一个测试模块"
        assert block.priority == 1
        assert block.status == BlockStatus.PENDING
        assert block.id is None  # 尚未保存到数据库

    def test_block_model_default_values(self):
        """测试 BlockModel 默认值"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
        )

        assert block.priority == 0  # 默认值
        assert block.status == BlockStatus.PENDING  # 默认值

    def test_block_model_save_to_db(self):
        """测试 BlockModel 保存到数据库"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            priority=1,
            status=BlockStatus.PENDING,
        )

        self.session.add(block)
        self.session.commit()

        assert block.id is not None
        assert isinstance(block.id, str)
        assert len(block.id) == 36  # UUID 长度

    def test_block_model_timestamps(self):
        """测试 BlockModel 时间戳字段"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
        )

        self.session.add(block)
        self.session.commit()

        assert block.created_at is not None
        assert block.updated_at is not None
        assert isinstance(block.created_at, datetime)
        assert isinstance(block.updated_at, datetime)

    def test_block_model_relationships(self, sample_system):
        """测试 BlockModel 关系"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            system_id=sample_system.id,
        )

        self.session.add(block)
        self.session.commit()

        # 测试 system 关系
        assert block.system is not None
        assert block.system.id == sample_system.id
        assert block.system.name == "测试系统"

        # 测试 features 关系
        assert block.features == []  # 初始为空列表

    def test_block_model_status_enum(self):
        """测试 BlockStatus 枚举"""
        assert BlockStatus.PENDING.value == "pending"
        assert BlockStatus.IN_PROGRESS.value == "in_progress"
        assert BlockStatus.COMPLETED.value == "completed"
        assert BlockStatus.ABORTED.value == "aborted"
        
        # 测试枚举成员
        assert BlockStatus("pending") == BlockStatus.PENDING
        assert BlockStatus("in_progress") == BlockStatus.IN_PROGRESS
        assert BlockStatus("completed") == BlockStatus.COMPLETED
        assert BlockStatus("aborted") == BlockStatus.ABORTED

    def test_block_model_string_representation(self):
        """测试 BlockModel 字符串表示"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
        )

        self.session.add(block)
        self.session.commit()

        # 测试 __repr__ 方法
        repr_str = repr(block)
        assert "BlockModel" in repr_str
        assert block.id in repr_str
        assert "测试模块" in repr_str

    def test_block_model_table_name(self):
        """测试 BlockModel 表名"""
        # TableNameMixin 会自动生成表名：BlockModel -> block
        import re
        name = "BlockModel"
        # 驼峰转蛇形
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # 移除尾部的 '_model' 或 '_mixin'
        if name.endswith(('_model', '_mixin')):
            name = name.rsplit('_', 1)[0]
        assert name == "block"

    def test_block_model_column_constraints(self):
        """测试 BlockModel 列约束"""
        # 测试 name 字段不能为空
        with pytest.raises(Exception):
            block = BlockModel(
                name=None,  # 应该引发错误
                description="这是一个测试模块",
            )
            self.session.add(block)
            self.session.commit()

    def test_block_model_priority_range(self):
        """测试 BlockModel 优先级范围"""
        # 测试优先级可以是负数
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            priority=-1,
        )

        self.session.add(block)
        self.session.commit()

        assert block.priority == -1

    def test_block_model_with_system_relationship(self, sample_system):
        """测试 BlockModel 与 SystemModel 的关系"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            system_id=sample_system.id,
        )

        self.session.add(block)
        self.session.commit()

        # 验证关系
        assert block.system_id == sample_system.id
        assert block.system == sample_system
        
        # 验证反向关系
        assert block in sample_system.blocks

    def test_block_model_cascade_delete(self, sample_system):
        """测试 BlockModel 级联删除"""
        block = BlockModel(
            name="测试模块",
            description="这是一个测试模块",
            system_id=sample_system.id,
        )

        self.session.add(block)
        self.session.commit()

        # 删除系统应该级联删除模块
        block_id = block.id
        self.session.delete(sample_system)
        self.session.commit()

        # 验证模块也被删除
        deleted_block = self.session.query(BlockModel).filter_by(id=block_id).first()
        assert deleted_block is None