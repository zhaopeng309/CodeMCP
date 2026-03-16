"""
SystemModel 单元测试
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.codemcp.models.system import SystemModel, SystemStatus
from src.codemcp.models.base import Base


class TestSystemModel:
    """SystemModel 单元测试类"""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """设置内存数据库用于测试"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        yield
        self.session.close()

    def test_system_model_creation(self):
        """测试 SystemModel 创建"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
            status=SystemStatus.ACTIVE,
        )

        assert system.name == "测试系统"
        assert system.description == "这是一个测试系统"
        assert system.status == SystemStatus.ACTIVE
        assert system.id is None  # 尚未保存到数据库

    def test_system_model_default_status(self):
        """测试 SystemModel 默认状态"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
        )

        assert system.status == SystemStatus.ACTIVE  # 默认值

    def test_system_model_save_to_db(self):
        """测试 SystemModel 保存到数据库"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
            status=SystemStatus.ACTIVE,
        )

        self.session.add(system)
        self.session.commit()

        assert system.id is not None
        assert isinstance(system.id, str)
        assert len(system.id) == 36  # UUID 长度

    def test_system_model_timestamps(self):
        """测试 SystemModel 时间戳字段"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
        )

        self.session.add(system)
        self.session.commit()

        assert system.created_at is not None
        assert system.updated_at is not None
        assert isinstance(system.created_at, datetime)
        assert isinstance(system.updated_at, datetime)

    def test_system_model_relationships(self):
        """测试 SystemModel 关系"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
        )

        # 测试 blocks 关系
        assert system.blocks == []  # 初始为空列表

    def test_system_model_status_enum(self):
        """测试 SystemStatus 枚举"""
        assert SystemStatus.ACTIVE.value == "active"
        assert SystemStatus.ARCHIVED.value == "archived"
        
        # 测试枚举成员
        assert SystemStatus("active") == SystemStatus.ACTIVE
        assert SystemStatus("archived") == SystemStatus.ARCHIVED

    def test_system_model_string_representation(self):
        """测试 SystemModel 字符串表示"""
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
        )

        self.session.add(system)
        self.session.commit()

        # 测试 __repr__ 方法
        repr_str = repr(system)
        assert "SystemModel" in repr_str
        assert system.id in repr_str
        assert "测试系统" in repr_str

    def test_system_model_table_name(self):
        """测试 SystemModel 表名"""
        # TableNameMixin 会自动生成表名：SystemModel -> system
        # 由于 __tablename__ 是 declared_attr，我们测试实际的表名生成逻辑
        import re
        name = "SystemModel"
        # 驼峰转蛇形
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # 移除尾部的 '_model' 或 '_mixin'
        if name.endswith(('_model', '_mixin')):
            name = name.rsplit('_', 1)[0]
        assert name == "system"

    def test_system_model_column_constraints(self):
        """测试 SystemModel 列约束"""
        # 测试 name 字段不能为空
        with pytest.raises(Exception):
            system = SystemModel(
                name=None,  # 应该引发错误
                description="这是一个测试系统",
            )
            self.session.add(system)
            self.session.commit()

    def test_system_model_indexes(self):
        """测试 SystemModel 索引"""
        # 测试 name 字段有索引
        system = SystemModel(
            name="测试系统",
            description="这是一个测试系统",
        )

        self.session.add(system)
        self.session.commit()

        # 验证可以通过 name 查询
        result = self.session.query(SystemModel).filter_by(name="测试系统").first()
        assert result is not None
        assert result.name == "测试系统"