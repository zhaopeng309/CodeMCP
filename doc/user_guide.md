# CodeMCP 用户指南

## 目录

1. [简介](#简介)
2. [核心概念](#核心概念)
3. [安装与配置](#安装与配置)
4. [快速入门](#快速入门)
5. [Gateway API 使用](#gateway-api-使用)
6. [Console CLI 使用](#console-cli-使用)
7. [MCP 协议集成](#mcp-协议集成)
8. [任务管理](#任务管理)
9. [故障排除](#故障排除)
10. [最佳实践](#最佳实践)

## 简介

CodeMCP 是一个基于 MCP（Model Context Protocol）协议的 AI 协同编排与执行服务器。它允许您：

- 协调多个 AI agent 协同完成软件开发任务
- 管理复杂的任务依赖关系和执行顺序
- 实现任务的自我修复和自动重试
- 通过交互式控制台监控和管理执行过程

### 目标用户

- **AI 开发者**: 需要协调多个 AI agent 完成复杂任务
- **DevOps 工程师**: 需要自动化测试和部署流程
- **项目经理**: 需要跟踪 AI 辅助开发进度
- **质量保证团队**: 需要自动化测试执行和报告

## 核心概念

### 四层数据模型

CodeMCP 使用四层数据模型来组织和管理任务：

1. **System（系统）**: 最高级别的业务领域或项目实例
   - 例如："电商平台"、"移动应用"、"后端服务"
   - 每个 System 独立运行，逻辑隔离

2. **Block（模块）**: 属于 System 的功能模块
   - 例如："用户认证模块"、"支付模块"、"商品管理模块"
   - Block 包含多个 Feature

3. **Feature（功能）**: 具体的功能点，属于 Block
   - 例如："用户注册功能"、"微信支付集成"、"商品搜索"
   - Feature 包含多个 Test

4. **Test（测试）**: 物理验证单元，属于 Feature
   - 例如："用户注册API测试"、"支付回调测试"
   - Test 是实际执行的最小单位

### 任务状态

任务在系统中流转的状态：

- **pending（待处理）**: 任务已创建，等待执行
- **running（运行中）**: 任务正在执行
- **passed（通过）**: 任务执行成功
- **failed（失败）**: 任务执行失败
- **aborted（中止）**: 任务被手动中止
- **retrying（重试中）**: 任务正在重试

### 执行窗口

CodeMCP 使用固定大小的执行窗口来限制并发任务数量：

- **默认窗口深度**: 5个并发任务
- **优先级调度**: 高优先级任务优先执行
- **窗口管理**: 任务完成后自动从窗口移除，新任务加入

## 安装与配置

### 系统要求

- Python 3.9 或更高版本
- SQLite（开发环境）或 PostgreSQL（生产环境）
- 至少 2GB 可用内存
- 网络连接（用于 MCP 协议通信）

### 安装步骤

#### 1. 获取代码

```bash
git clone https://github.com/zhaopeng309/CodeMCP.git
cd codemcp
```

#### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

#### 3. 安装依赖

```bash
# 基础安装
pip install -e .

# 包含开发工具
pip install -e .[dev]

# 包含文档工具
pip install -e .[docs]
```

#### 4. 环境配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，主要配置项：

```env
# 数据库配置
DATABASE_URL=sqlite:///./codemcp.db  # 开发环境
# DATABASE_URL=postgresql://user:password@localhost/codemcp  # 生产环境

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# 任务配置
TASK_WINDOW_SIZE=5
MAX_RETRIES=3
RETRY_DELAY=5

# MCP 配置
MCP_PLANNER_URL=http://localhost:8080
MCP_EXECUTOR_URL=http://localhost:8081
```

#### 5. 初始化数据库

```bash
# 应用数据库迁移
alembic upgrade head

# 验证数据库
python -c "from codemcp.database.engine import engine; print('数据库连接成功')"
```

## 快速入门

### 启动服务

#### 启动 Gateway 服务器

```bash
# 方式一：使用内置命令
codemcp-server

# 方式二：直接运行 FastAPI
uvicorn codemcp.api.server:app --host 0.0.0.0 --port 8000 --reload
```

服务器启动后，访问以下地址：
- API 文档: http://localhost:8000/docs
- Redoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

#### 启动 Console CLI

```bash
# 交互式控制台
codemcp

# 或直接运行特定命令
codemcp monitor --follow
```

### 创建第一个 System

#### 使用 API

```bash
curl -X POST "http://localhost:8000/api/v1/systems" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "电商平台",
    "description": "在线购物平台开发项目",
    "config": {
      "repository_url": "https://github.com/zhaopeng309/CodeMCP",
      "branch": "main"
    }
  }'
```

#### 使用 Console CLI

```bash
codemcp system create \
  --name "电商平台" \
  --description "在线购物平台开发项目" \
  --config '{"repository_url": "https://github.com/zhaopeng309/CodeMCP", "branch": "main"}'
```

### 提交执行计划

通过 MCP 协议或直接 API 提交计划：

```bash
curl -X POST "http://localhost:8000/api/v1/plans" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": 1,
    "plan_data": {
      "blocks": [
        {
          "name": "用户认证模块",
          "features": [
            {
              "name": "用户注册",
              "tests": [
                {"name": "注册API测试", "command": "pytest tests/test_auth.py::test_register"},
                {"name": "邮箱验证测试", "command": "pytest tests/test_auth.py::test_email_verification"}
              ]
            }
          ]
        }
      ]
    }
  }'
```

## Gateway API 使用

### 认证和授权

目前 API 使用简单的 API Key 认证：

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/systems
```

### 主要 API 端点

#### 系统管理

- `GET /api/v1/systems` - 获取所有系统
- `POST /api/v1/systems` - 创建新系统
- `GET /api/v1/systems/{system_id}` - 获取特定系统详情
- `PUT /api/v1/systems/{system_id}` - 更新系统
- `DELETE /api/v1/systems/{system_id}` - 删除系统

#### 任务管理

- `GET /api/v1/tasks` - 获取任务列表（支持过滤）
- `GET /api/v1/tasks/next` - 获取下一个待执行任务
- `PUT /api/v1/tasks/{task_id}/result` - 提交任务结果
- `POST /api/v1/tasks/{task_id}/retry` - 重试失败任务
- `POST /api/v1/tasks/{task_id}/abort` - 中止任务

#### 队列管理

- `GET /api/v1/queue` - 获取队列状态
- `POST /api/v1/queue/pause` - 暂停任务分发
- `POST /api/v1/queue/resume` - 恢复任务分发
- `POST /api/v1/queue/clear` - 清空待处理队列

#### 监控和统计

- `GET /api/v1/status` - 获取系统整体状态
- `GET /api/v1/stats` - 获取统计信息
- `GET /api/v1/events` - 获取事件历史
- `GET /api/v1/logs` - 获取执行日志

### WebSocket 接口

#### 实时事件

连接到 WebSocket 端点获取实时事件：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到事件:', data);
  
  // 事件类型包括：
  // - task_created: 任务创建
  // - task_started: 任务开始执行
  // - task_completed: 任务完成
  // - task_failed: 任务失败
  // - task_retrying: 任务重试
  // - system_status_changed: 系统状态变更
};
```

#### 实时日志

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/logs');

ws.onmessage = (event) => {
  const logEntry = JSON.parse(event.data);
  console.log(`[${logEntry.timestamp}] ${logEntry.level}: ${logEntry.message}`);
};
```

## Console CLI 使用

### 交互式模式

启动交互式控制台：

```bash
codemcp
```

交互式控制台提供以下功能：
- 实时监控面板
- 任务队列管理
- 系统状态查看
- 手动任务操作

### 命令参考

#### 监控命令

```bash
# 实时监控（跟随模式）
codemcp monitor --follow

# 监控特定系统
codemcp monitor --system 1

# 监控特定任务类型
codemcp monitor --type test

# 输出为 JSON 格式
codemcp monitor --json
```

#### 队列管理

```bash
# 查看队列状态
codemcp queue status

# 暂停任务分发
codemcp queue pause

# 恢复任务分发
codemcp queue resume

# 清空待处理队列
codemcp queue clear --confirm

# 调整队列优先级
codemcp queue prioritize --task-id 123 --priority high
```

#### 系统管理

```bash
# 列出所有系统
codemcp system list

# 创建新系统
codemcp system create --name "项目名称" --description "项目描述"

# 查看系统详情
codemcp system show 1

# 更新系统配置
codemcp system update 1 --config '{"new_setting": "value"}'

# 删除系统
codemcp system delete 1 --confirm
```

#### 任务操作

```bash
# 列出任务
codemcp task list --status pending
codemcp task list --system 1
codemcp task list --block "用户认证"

# 手动重试任务
codemcp task retry 123

# 中止任务
codemcp task abort 123 --reason "手动中止"

# 强制标记为通过
codemcp task pass 123 --force

# 查看任务日志
codemcp task logs 123
```

#### 统计和报告

```bash
# 系统整体统计
codemcp stats overview

# 时间段统计
codemcp stats --start "2024-01-01" --end "2024-01-31"

# 生成报告
codemcp report generate --format html --output report.html
codemcp report generate --format json --output stats.json
```

### 快捷键参考

在交互式控制台中：

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+C` | 退出程序 |
| `h` | 显示帮助 |
| `m` | 切换到监控视图 |
| `q` | 切换到队列视图 |
| `s` | 切换到系统视图 |
| `r` | 刷新当前视图 |
| `↑/↓` | 上下导航 |
| `Enter` | 选择/确认 |
| `Space` | 暂停/恢复自动刷新 |

## MCP 协议集成

### Planner 集成

Planner 是通过 MCP 协议与 CodeMCP 通信的外部 AI，负责创建执行计划。

#### MCP 端点

- `mcp://codemcp/plan/create` - 创建新计划
- `mcp://codemcp/plan/status` - 查询计划状态
- `mcp://codemcp/system/list` - 获取系统列表

#### 示例：Python 客户端

```python
import httpx
from mcp import Client

async def create_plan():
    async with Client("http://localhost:8000/mcp") as client:
        # 创建计划
        response = await client.call(
            "mcp://codemcp/plan/create",
            {
                "system_id": 1,
                "requirements": "实现用户登录功能，包括邮箱验证和密码重置",
                "constraints": "使用JWT认证，支持OAuth2.0"
            }
        )
        
        plan_id = response["plan_id"]
        print(f"计划创建成功: {plan_id}")
```

### Executor 集成

Executor 是执行具体测试任务的外部 agent。

#### 任务获取

```python
async def fetch_task():
    async with httpx.AsyncClient() as client:
        # 获取下一个任务
        response = await client.get(
            "http://localhost:8000/api/v1/tasks/next",
            headers={"X-API-Key": "your-api-key"}
        )
        
        if response.status_code == 200:
            task = response.json()
            return task
        else:
            return None
```

#### 提交结果

```python
async def submit_result(task_id, passed, output):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://localhost:8000/api/v1/tasks/{task_id}/result",
            json={
                "passed": passed,
                "output": output,
                "execution_time": 15.5  # 执行时间（秒）
            },
            headers={"X-API-Key": "your-api-key"}
        )
        
        return response.status_code == 200
```

## 任务管理

### 任务生命周期

1. **计划创建**: Planner 创建包含多个任务的结构化计划
2. **任务分发**: Gateway 将任务分配到执行窗口
3. **任务执行**: Executor 获取并执行任务
4. **结果提交**: Executor 提交执行结果
5. **状态更新**: Gateway 更新任务状态，触发后续操作

### 失败处理流程

当任务失败时：

1. **自动重试**: 系统自动重试失败任务（最多3次）
2. **重试间隔**: 每次重试之间有延迟（默认5秒）
3. **级联中止**: 如果重试全部失败，中止所属 Block 的所有任务
4. **重新规划**: 通知 Planner 重新规划更细粒度的任务
5. **人工干预**: 用户可以通过 Console 手动处理

### 优先级管理

任务优先级分为：

- **critical（关键）**: 最高优先级，立即执行
- **high（高）**: 高优先级，优先于普通任务
- **normal（普通）**: 默认优先级
- **low（低）**: 低优先级，最后执行

设置优先级：

```bash
# 创建高优先级任务
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "紧急安全修复",
    "command": "pytest tests/security/test_auth.py",
    "priority": "critical"
  }'
```

## 故障排除

### 常见问题

#### 1. 数据库连接失败

**症状**: 启动服务时出现数据库连接错误

**解决方案**:
```bash
# 检查数据库文件权限
chmod 644 codemcp.db

# 检查 SQLite 文件完整性
sqlite3 codemcp.db "PRAGMA integrity_check;"

# 重新初始化数据库
rm codemcp.db
alembic upgrade head
```

#### 2. 任务卡在 pending 状态

**症状**: 任务一直处于 pending 状态，不执行

**解决方案**:
```bash
# 检查队列状态
codemcp queue status

# 检查执行窗口是否已满
codemcp status

# 手动触发任务分发
curl -X POST "http://localhost:8000/api/v1/queue/resume"
```

#### 3. WebSocket 连接失败

**症状**: 实时监控无法连接

**解决方案**:
```bash
# 检查服务器是否运行
curl http://localhost:8000/health

# 检查防火墙设置
sudo ufw allow 8000/tcp

# 检查 WebSocket 支持
curl -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws/events
```

#### 4. 内存使用过高

**症状**: 系统变慢，内存占用持续增长

**解决方案**:
```bash
# 减少并发任务数
export TASK_WINDOW_SIZE=3

# 清理旧日志
codemcp logs cleanup --days 7

# 重启服务
codemcp-server --restart
```

### 日志查看

#### 查看服务日志

```bash
# 查看实时日志
tail -f logs/codemcp.log

# 按级别过滤
grep "ERROR" logs/codemcp.log

# 查看特定时间段的日志
journalctl -u codemcp --since "2024-01-15" --until "2024-01-16"
```

#### 查看任务日志

```bash
# 通过 CLI 查看
codemcp task logs 123

# 通过