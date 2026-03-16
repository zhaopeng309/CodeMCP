# CodeMCP 项目架构设计

## 项目概述
CodeMCP 是一个基于 MCP（Model Context Protocol）协议的 AI 协同编排与执行服务器，支持多个 agent 协同执行软件开发任务。系统通过四个核心角色构建了一个具备"自我修复"能力的 AI 生产力闭环。

## 系统架构

### 核心组件
```
┌─────────────────────────────────────────────────────────────┐
│                    Planner (规划内核)                        │
│  • 顶层逻辑拆解                                              │
│  • 生成结构化计划 (System → Block → Feature → Test)         │
│  • 通过 MCP 协议与 CodeMCP 交互                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ MCP Protocol
┌───────────────────────▼─────────────────────────────────────┐
│                    CodeMCP Server                           │
├─────────────────────────────────────────────────────────────┤
│  Gateway (通信中枢)        │  Console (管理控制台)          │
│  • FastAPI REST API        │  • Python CLI                  │
│  • 状态机管理              │  • 任务队列管理                │
│  • 任务窗口化执行          │  • 实时监控                    │
│  • SQLAlchemy 持久化       │  • 人工干预接口                │
└──────────────┬──────────────────────────────┬──────────────┘
               │                              │
        ┌──────▼──────┐                ┌──────▼──────┐
        │   Database  │                │   Executor  │
        │  (SQLite)   │                │  (外部Agent)│
        └─────────────┘                └─────────────┘
```

### 数据流
1. **计划导入**: Planner → Gateway → Database
2. **任务执行**: Gateway → Executor → Test Execution → Gateway → Database
3. **状态监控**: Console ← Database → Gateway
4. **失败处理**: Test Failure → Gateway → Console → Planner → 重新规划

## 技术栈
- **编程语言**: Python 3.9+
- **Web框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: SQLite (开发), 支持 PostgreSQL (生产)
- **CLI框架**: Click 或 Typer
- **测试框架**: pytest (用于项目自身测试)
- **依赖管理**: Poetry 或 pip + requirements.txt
- **日志系统**: Python logging + structlog (可选)

## 四层数据模型设计

### 1. System (业务领域)
- 代表独立的业务领域或项目实例
- 属性: id, name, description, created_at, updated_at
- 状态: active, archived

### 2. Block (功能模块)
- 属于某个 System 的功能模块
- 属性: id, system_id, name, description, priority
- 状态: pending, in_progress, completed, aborted

### 3. Feature (功能点)
- 属于某个 Block 的具体功能点
- 属性: id, block_id, name, description, test_command
- 状态: pending, running, passed, failed, aborted

### 4. Test (测试单元)
- 属于某个 Feature 的物理验证单元
- 属性: id, feature_id, command, exit_code, stdout, stderr, duration
- 状态: pending, running, passed, failed

## 状态机设计

### 任务状态流转
```
Pending → Running → [Passed | Failed]
Failed → Aborted (Block级别) → Pending (重新规划后)
```

### 窗口化执行机制
- Gateway 维护深度为 5 的执行窗口
- 只有窗口内的任务可以进入 Running 状态
- 任务完成后释放窗口位置

## API 设计

### Gateway REST API
```
POST   /api/v1/plans          # 导入计划
GET    /api/v1/tasks/next     # 获取下一个待执行任务
POST   /api/v1/tasks/{id}/start    # 开始执行任务
POST   /api/v1/tasks/{id}/complete # 完成任务
POST   /api/v1/tasks/{id}/fail     # 标记任务失败
GET    /api/v1/status         # 系统状态
POST   /api/v1/queue/pause    # 暂停队列
POST   /api/v1/queue/resume   # 恢复队列
```

### Console CLI 命令
```
codemcp monitor --follow      # 实时监控
codemcp queue --block         # 暂停任务分发
codemcp queue --clear         # 清空待处理队列
codemcp status --system <ID>  # 系统状态统计
codemcp task --retry <ID>     # 重试失败任务
codemcp task --abort <ID>     # 中止任务
codemcp db --reset            # 重置数据库
```

## MCP 协议接口

### Planner 接口
```
mcp://codemcp/plan/create     # 创建计划
mcp://codemcp/plan/update     # 更新计划
mcp://codemcp/task/status     # 查询任务状态
```

### Executor 接口
```
mcp://codemcp/task/fetch      # 获取待执行任务
mcp://codemcp/task/result     # 提交任务结果
```

## 项目结构
```
codemcp/
├── src/
│   └── codemcp/
│       ├── __init__.py
│       ├── models/           # 数据模型
│       │   ├── __init__.py
│       │   ├── system.py
│       │   ├── block.py
│       │   ├── feature.py
│       │   └── test.py
│       ├── api/              # Gateway API
│       │   ├── __init__.py
│       │   ├── dependencies.py
│       │   ├── routes/
│       │   │   ├── plans.py
│       │   │   ├── tasks.py
│       │   │   └── queue.py
│       │   └── server.py
│       ├── cli/              # Console CLI
│       │   ├── __init__.py
│       │   ├── commands/
│       │   │   ├── monitor.py
│       │   │   ├── queue.py
│       │   │   ├── status.py
│       │   │   └── task.py
│       │   └── main.py
│       ├── core/             # 核心逻辑
│       │   ├── __init__.py
│       │   ├── state_machine.py
│       │   ├── task_window.py
│       │   └── executor.py
│       ├── database/         # 数据库层
│       │   ├── __init__.py
│       │   ├── session.py
│       │   └── migrations/
│       └── mcp/              # MCP协议实现
│           ├── __init__.py
│           ├── planner.py
│           └── executor.py
├── tests/                    # 测试文件
├── pyproject.toml           # 项目配置
├── README.md               # 项目文档
└── Dockerfile              # 容器化配置
```

## 关键特性实现

### 1. 自我修复机制
- 当 Test 失败时，自动将所属 Block 标记为 Aborted
- 通知 Console 显示红色警告
- 支持 Planner 重新规划更细粒度的任务

### 2. 人工接管 (HITL)
- Console 提供完整的队列管理功能
- 支持实时暂停、恢复、清理操作
- 允许手动修正任务状态

### 3. 确定性回滚
- 每个任务执行前记录 Git 状态（由上层 Planner 负责）
- 失败时支持回滚到安全点

## 下一步行动
1. 详细设计数据模型和数据库 schema
2. 定义完整的 API 接口规范
3. 设计 Console CLI 的具体命令参数
4. 创建项目基础结构
5. 实现核心状态机逻辑