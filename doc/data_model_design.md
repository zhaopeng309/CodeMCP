# CodeMCP 数据模型设计

## 数据库 Schema 设计

### 1. System 表 (业务领域)
```python
class System(Base):
    __tablename__ = "systems"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum("active", "archived"), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    blocks = relationship("Block", back_populates="system", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index("ix_systems_status", "status"),
    )
```

### 2. Block 表 (功能模块)
```python
class Block(Base):
    __tablename__ = "blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("systems.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=0, nullable=False)  # 优先级，数字越小优先级越高
    status = Column(
        Enum("pending", "in_progress", "completed", "aborted"),
        default="pending",
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    system = relationship("System", back_populates="blocks")
    features = relationship("Feature", back_populates="block", cascade="all, delete-orphan")
    
    # 复合索引
    __table_args__ = (
        Index("ix_blocks_system_status", "system_id", "status"),
        Index("ix_blocks_priority", "priority"),
    )
```

### 3. Feature 表 (功能点)
```python
class Feature(Base):
    __tablename__ = "features"
    
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_command = Column(Text, nullable=False)  # 测试命令，如 "pytest tests/test_feature.py"
    status = Column(
        Enum("pending", "running", "passed", "failed", "aborted"),
        default="pending",
        nullable=False
    )
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    block = relationship("Block", back_populates="features")
    tests = relationship("Test", back_populates="feature", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index("ix_features_block_status", "block_id", "status"),
        Index("ix_features_status_created", "status", "created_at"),
    )
```

### 4. Test 表 (测试单元)
```python
class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("features.id", ondelete="CASCADE"), nullable=False)
    command = Column(Text, nullable=False)  # 实际执行的命令
    exit_code = Column(Integer, nullable=True)  # 退出码，0表示成功
    stdout = Column(Text, nullable=True)  # 标准输出
    stderr = Column(Text, nullable=True)  # 标准错误
    duration = Column(Float, nullable=True)  # 执行时长（秒）
    status = Column(
        Enum("pending", "running", "passed", "failed"),
        default="pending",
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    feature = relationship("Feature", back_populates="tests")
    
    # 索引
    __table_args__ = (
        Index("ix_tests_feature_status", "feature_id", "status"),
        Index("ix_tests_exit_code", "exit_code"),
    )
```

### 5. TaskQueue 表 (任务队列 - 可选)
```python
class TaskQueue(Base):
    __tablename__ = "task_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("features.id", ondelete="CASCADE"), nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    status = Column(
        Enum("pending", "in_window", "processing", "completed", "failed"),
        default="pending",
        nullable=False
    )
    window_position = Column(Integer, nullable=True)  # 在窗口中的位置（1-5）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    feature = relationship("Feature")
    
    # 索引
    __table_args__ = (
        Index("ix_task_queue_status_priority", "status", "priority", "created_at"),
        Index("ix_task_queue_window", "window_position"),
    )
```

## 数据模型关系图
```
System (1) ──┐
             ├── (1..*) Block (1) ──┐
                                    ├── (1..*) Feature (1) ──┐
                                                             ├── (1..*) Test
                                                             └── (0..1) TaskQueue
```

## 状态流转规则

### Block 状态规则
1. **pending**: 初始状态，所有 Feature 都处于 pending
2. **in_progress**: 至少有一个 Feature 处于 running 状态
3. **completed**: 所有 Feature 都处于 passed 状态
4. **aborted**: 任意一个 Feature 处于 aborted 状态，或手动中止

### Feature 状态规则
1. **pending**: 初始状态
2. **running**: 任务开始执行
3. **passed**: 关联的所有 Test 都通过（exit_code == 0）
4. **failed**: 任意一个 Test 失败（exit_code != 0）且重试次数用尽
5. **aborted**: 手动中止或所属 Block 被中止

### 级联更新逻辑
- 当 Feature 状态变为 failed 且 retry_count >= max_retries 时：
  - 所属 Block 状态自动变为 aborted
  - Block 下所有其他 pending/running 的 Feature 状态变为 aborted

## 查询优化考虑

### 常用查询场景
1. **获取待执行任务**：`SELECT * FROM features WHERE status = 'pending' ORDER BY priority, created_at LIMIT 5`
2. **系统状态统计**：按 System 分组统计 Feature 完成率
3. **实时监控**：最近更新的任务和测试结果
4. **失败分析**：失败的 Test 及其错误输出

### 性能优化
1. 为频繁查询的字段创建索引
2. 使用数据库连接池
3. 考虑分表策略（如果数据量巨大）
4. 定期归档已完成的历史数据

## 下一步
1. 设计 API 接口的数据传输对象（DTO）
2. 定义数据库迁移策略（Alembic）
3. 设计数据验证规则
4. 规划缓存策略（如果需要）