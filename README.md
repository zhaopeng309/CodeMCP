# CodeMCP - AI协同编排与执行服务器

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

CodeMCP 是一个基于 **MCP（Model Context Protocol）协议** 的 AI 协同编排与执行服务器，支持多个 AI agent 协同执行软件开发任务。系统通过四层数据模型和状态机管理，构建了一个具备"自我修复"能力的 AI 生产力闭环。

## ✨ 核心特性

### 🤖 多Agent协同
- **四角色架构**: Planner、Gateway、Console、Executor 协同工作
- **MCP协议支持**: 标准化的 AI 通信接口
- **任务编排**: 智能调度和优先级管理

### 🔄 自我修复能力
- **自动重试机制**: 失败任务自动重试（最多3次）
- **级联中止**: 重试失败后自动中止所属模块
- **重新规划**: Planner 可重新规划更细粒度的任务
- **确定性回滚**: 结合 Git 的状态回滚机制

### 🎯 确定性交付
- **硬核测试验证**: 任务交付以测试通过为准
- **Git状态记录**: 执行前记录代码状态，支持安全回滚
- **完整审计**: 全链路日志和测试结果记录

### 🛠️ 人工接管（HITL）
- **交互式控制台**: 实时监控和管理界面
- **队列管理**: 支持暂停、恢复、清理操作
- **状态修正**: 允许手动调整任务状态和优先级

## 📊 系统架构

### 四层数据模型
```
System (系统) → Block (模块) → Feature (功能) → Test (测试)
```

### 核心组件
1. **Planner** - 外部 AI，通过 MCP 协议创建结构化计划
2. **Gateway** - FastAPI 服务器，管理状态机、任务窗口和持久化
3. **Console** - 交互式 CLI（Typer + prompt-toolkit），用于监控和人工干预
4. **Executor** - 外部 agent，执行单个测试任务

### 状态管理
- **任务状态流转**: `pending` → `running` → `passed`/`failed`
- **执行窗口**: 固定大小（默认深度5），限制并发运行任务
- **失败处理**: 自动重试、级联中止、重新规划

## 🚀 快速开始

### 环境要求
- Python 3.9+
- SQLite（开发）或 PostgreSQL（生产）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd CodeMCP
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -e .[dev]
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，根据需要调整配置
   ```

5. **初始化数据库**
   ```bash
   alembic upgrade head
   ```

### 运行服务

#### 使用启动脚本（推荐）
项目根目录提供了完整的启动脚本 `start.sh`，支持一键启动和多种操作模式：

```bash
# 给予执行权限（首次使用）
chmod +x start.sh

# 查看帮助信息
./start.sh --help

# 启动完整开发环境（推荐）
./start.sh --dev

# 只初始化环境（安装依赖、初始化数据库）
./start.sh --init

# 只启动服务器
./start.sh --server --dev

# 只启动CLI控制台
./start.sh --cli

# 运行测试
./start.sh --test

# 构建文档
./start.sh --docs

# 清理环境
./start.sh --clean
```

#### 使用命令行工具包装器（推荐）
项目提供了多个命令行工具包装器，位于 `bin/` 目录下，方便直接使用：

```bash
# 给予执行权限（首次使用）
chmod +x bin/*

# 交互式控制台（提示符为 code_shell>）
./bin/code_shell

# 启动API服务器
./bin/codemcp-server --host 0.0.0.0 --port 8000 --reload

# 数据库管理
./bin/codemcp-db init      # 初始化数据库
./bin/codemcp-db check     # 检查数据库连接
./bin/codemcp-db migrate   # 运行数据库迁移

# 通用CLI（无参数时启动交互式控制台）
./bin/codemcp              # 启动交互式控制台
./bin/codemcp monitor      # 监控模式
./bin/codemcp status       # 查看系统状态

# 开发工具
./bin/codemcp-dev test     # 运行测试
./bin/codemcp-dev lint     # 代码检查
./bin/codemcp-dev format   # 代码格式化
```

#### 启动 Gateway 服务器
```bash
# 方式一：使用包装器脚本（推荐）
./bin/codemcp-server --host 0.0.0.0 --port 8000 --reload

# 方式二：使用内置命令
codemcp-server

# 方式三：直接运行
uvicorn codemcp.api.server:app --host 0.0.0.0 --port 8000 --reload
```

#### 使用 Console CLI
```bash
# 启动交互式控制台（使用包装器）
./bin/code_shell

# 或使用通用CLI
./bin/codemcp

# 实时监控
codemcp monitor --follow

# 队列管理
codemcp queue --block

# 系统状态查看
codemcp status --system <系统ID>
```

## 📖 详细文档

- [项目概述](doc/project_summary.md) - 项目整体规划和设计
- [架构设计](doc/architecture_design.md) - 系统架构详细说明
- [数据模型](doc/data_model_design.md) - 四层数据模型设计
- [API规范](doc/api_specification.md) - REST API 接口文档
- [MCP协议](doc/mcp_protocol_interface.md) - MCP 协议接口规范
- [控制台实现](doc/console_cli_implementation.md) - CLI 控制台设计
- [状态机设计](doc/state_machine_design.md) - 任务状态流转机制
- [任务窗口机制](doc/task_window_mechanism.md) - 执行窗口调度算法
- [测试策略](doc/testing_strategy.md) - 测试框架和策略
- [部署指南](doc/documentation_and_deployment.md) - 生产环境部署

## 🔧 开发指南

### 项目结构
```
codemcp/
├── src/codemcp/
│   ├── models/          # 数据模型层
│   ├── database/        # 数据库层
│   ├── api/            # Gateway API
│   ├── core/           # 核心业务逻辑
│   ├── cli/            # 命令行界面
│   ├── mcp/            # MCP 协议实现
│   └── utils/          # 工具函数
├── tests/              # 测试代码
├── doc/               # 项目文档
└── scripts/           # 构建和部署脚本
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试模块
pytest tests/test_models/test_system.py

# 生成覆盖率报告
pytest --cov=src/codemcp --cov-report=html
```

### 代码质量
```bash
# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

## 🌐 API 接口

### 主要端点
- `POST /api/v1/plans` - 提交新的执行计划
- `GET /api/v1/tasks/next` - 获取下一个待执行任务
- `PUT /api/v1/tasks/{task_id}/result` - 提交任务执行结果
- `GET /api/v1/systems` - 获取系统列表
- `GET /api/v1/status` - 获取系统状态

### WebSocket 事件
- `ws://localhost:8000/ws/events` - 实时事件推送
- `ws://localhost:8000/ws/logs` - 实时日志流

## 🐳 Docker 部署

### 使用 Docker Compose
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 构建自定义镜像
```bash
docker build -t codemcp:latest .
docker run -p 8000:8000 --env-file .env codemcp:latest
```

## 📈 监控和运维

### 内置监控
- **实时仪表盘**: Console CLI 提供实时监控界面
- **事件日志**: WebSocket 推送所有状态变更事件
- **性能指标**: 任务执行时间、成功率等统计

### 外部集成
- **Prometheus**: 性能指标导出
- **Grafana**: 可视化仪表盘
- **ELK Stack**: 日志收集和分析

## 🤝 贡献指南

我们欢迎各种形式的贡献！请查看以下指南：

1. **报告问题**: 使用 GitHub Issues 报告 bug 或提出功能建议
2. **提交代码**: Fork 仓库，创建功能分支，提交 Pull Request
3. **代码规范**: 遵循项目的代码风格和测试要求
4. **文档更新**: 确保相关文档与代码变更同步

### 开发流程
1. 创建 issue 描述问题或功能
2. Fork 项目并创建功能分支
3. 实现功能并添加测试
4. 确保所有测试通过
5. 提交 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与联系

- **问题反馈**: [GitHub Issues](https://github.com/zhaopeng309/CodeMCP/issues)
- **文档**: [项目文档目录](doc/)
- **邮件**: team@codemcp.example.com

---

**CodeMCP** - 让 AI 协同开发更可靠、更高效！