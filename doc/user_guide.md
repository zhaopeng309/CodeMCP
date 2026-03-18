# CodeMCP 用户指南

## 目录

1. [简介](#简介)
2. [核心概念](#核心概念)
3. [安装与配置](#安装与配置)
4. [快速入门](#快速入门)
5. [Gateway API 使用](#gateway-api-使用)
6. [命令行工具包装器](#命令行工具包装器)
7. [Console CLI 使用](#console-cli-使用)
8. [MCP 协议集成](#mcp-协议集成)
9. [任务管理](#任务管理)
10. [故障排除](#故障排除)
11. [最佳实践](#最佳实践)

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

CodeMCP 支持可配置的 JWT（JSON Web Token）认证系统，通过环境变量 `AUTH_ENABLED` 控制是否启用认证。

#### 认证开关

在 `.env` 文件中配置：

```bash
# 如果设置为 false，所有 API 都不需要认证
# 如果设置为 true，需要 JWT 令牌认证
AUTH_ENABLED=true

# JWT 认证配置（当 AUTH_ENABLED=true 时生效）
SECRET_KEY=codemcp-secret-key-change-in-production
JWT_ALGORITHM=HS256

# 初始管理员账户（当 AUTH_ENABLED=true 时生效）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

#### 启用认证时的使用方式

1. **初始化管理员用户**：
   ```bash
   python scripts/init_admin.py
   ```

2. **获取访问令牌**：
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

3. **使用令牌访问 API**：
   ```bash
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/tasks/
   ```

#### 禁用认证时的使用方式

当 `AUTH_ENABLED=false` 时，所有 API 都不需要认证：

```bash
# 直接访问 API，无需令牌
curl http://localhost:8000/tasks/
curl http://localhost:8000/auth/me
```

#### 认证 API 端点

- `POST /auth/login` - 用户登录，获取 JWT 令牌
- `POST /auth/register` - 用户注册（仅当认证启用时可用）
- `POST /auth/logout` - 用户登出，撤销令牌
- `POST /auth/logout/all` - 撤销用户的所有令牌
- `GET /auth/me` - 获取当前用户信息
- `PUT /auth/me` - 更新当前用户信息
- `POST /auth/password/reset/request` - 请求密码重置
- `POST /auth/password/reset/confirm` - 确认密码重置
- `GET /auth/health` - 认证服务健康检查

#### 令牌特性

- **永不过期**：按照设计需求，JWT 令牌一旦设置永不过期
- **可撤销**：通过数据库记录支持令牌撤销
- **Bearer 格式**：使用标准的 `Authorization: Bearer <token>` 头

#### CLI 工具的项目级配置

CodeMCP 的 CLI 工具支持项目级配置文件，允许在不同项目中使用不同的配置。这对于多项目环境特别有用，每个项目可以有自己的认证配置、数据库连接等。

##### 配置文件优先级

CLI 工具按照以下优先级顺序加载配置文件（后读取的覆盖先读取的）：

1. **安装目录（CODEMCP_HOME）的 `.codemcp` 文件**（先读取）
2. **当前工作目录的 `.codemcp` 文件**（后读取，可以覆盖安装目录的配置）
3. **环境变量**
4. **默认值**

**注意**：pydantic-settings 会按顺序读取配置文件，后读取的文件会覆盖先读取的文件中的相同配置项。

##### 自动配置文件管理

当你在项目目录中运行 CLI 工具时，系统会自动处理配置文件：

1. **检查当前目录**：如果当前目录没有 `.codemcp` 文件
2. **从安装目录拷贝**：如果安装目录有 `.codemcp` 文件，自动拷贝到当前目录
3. **创建默认配置**：如果安装目录也没有配置文件，创建一个包含默认值的配置文件

##### 使用示例

```bash
# 1. 进入项目目录
cd /path/to/your/project

# 2. 运行 CLI 工具（首次运行会自动创建配置文件）
codemcp status

# 3. 查看自动创建的配置文件
cat .codemcp

# 4. 编辑项目级配置
nano .codemcp
```

##### 配置环境变量

为了支持项目级配置，需要设置 `CODEMCP_HOME` 环境变量指向安装目录：

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export CODEMCP_HOME="/path/to/CodeMCP/installation"

# 或者在运行命令时临时设置
CODEMCP_HOME="/path/to/CodeMCP/installation" codemcp status
```

##### 项目级配置示例

创建 `.codemcp` 文件来覆盖全局配置：

```bash
# 项目级配置文件示例 (.codemcp)

# 认证配置（覆盖全局配置）
AUTH_ENABLED=false  # 本项目禁用认证
SECRET_KEY=project-specific-secret-key

# 数据库配置（使用项目特定的数据库）
DATABASE_URL=sqlite:///./myproject.db

# 服务器配置
HOST=127.0.0.1
PORT=9000

# 任务执行配置
TASK_WINDOW_DEPTH=3
MAX_RETRY_COUNT=2
```

##### 配置覆盖规则

假设有以下配置：

1. **全局配置**（安装目录的 `.codemcp`）：
   ```bash
   AUTH_ENABLED=true
   SECRET_KEY=global-secret-key
   DATABASE_URL=sqlite:///./global.db
   PORT=8000
   ```

2. **项目配置**（当前目录的 `.codemcp`）：
   ```bash
   AUTH_ENABLED=false
   DATABASE_URL=sqlite:///./myproject.db
   ```

**最终生效的配置**：
- `AUTH_ENABLED=false`（项目级配置覆盖全局配置）
- `SECRET_KEY=global-secret-key`（使用全局配置，项目未覆盖）
- `DATABASE_URL=sqlite:///./myproject.db`（项目级配置覆盖全局配置）
- `PORT=8000`（使用全局配置，项目未覆盖）

##### 最佳实践

1. **敏感信息管理**：
   - 将 `.codemcp` 文件添加到 `.gitignore` 中，避免提交敏感信息
   - 使用环境变量或密钥管理服务存储生产环境的密钥

2. **团队协作**：
   - 提供 `.codemcp.example` 模板文件，包含配置说明但不包含敏感信息
   - 新成员可以通过复制模板快速配置

3. **多环境支持**：
   - 为开发、测试、生产环境创建不同的配置文件
   - 使用环境变量切换配置文件

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

## 命令行工具包装器

CodeMCP 提供了多个命令行工具包装器，位于 `bin/` 目录下，方便用户直接使用而无需记忆复杂的 Python 命令。

### bin 目录结构

```
bin/
├── code_shell          # 交互式控制台包装器
├── code_shell.py       # 交互式控制台 Python 脚本
├── codemcp             # 通用 CLI 包装器
├── codemcp-server      # API 服务器启动脚本
├── codemcp-db          # 数据库管理工具
└── codemcp-dev         # 开发工具
```

### 使用方法

#### 1. 交互式控制台 (code_shell)

启动交互式控制台，提示符为 `code_shell>`：

```bash
./bin/code_shell
```

或者使用 Python 脚本：

```bash
python bin/code_shell.py
```

交互式控制台功能：
- 实时监控面板显示系统状态
- 任务队列管理
- 命令历史记录和 Tab 补全
- 界面上方包含命令输入区域和 help 信息

#### 2. API 服务器启动 (codemcp-server)

启动 FastAPI 服务器：

```bash
./bin/codemcp-server
```

支持参数：
- `--host`: 监听主机（默认：0.0.0.0）
- `--port`: 监听端口（默认：8000）
- `--reload`: 开发模式热重载

示例：
```bash
./bin/codemcp-server --host 127.0.0.1 --port 8080 --reload
```

#### 3. 数据库管理 (codemcp-db)

数据库管理工具：

```bash
./bin/codemcp-db init      # 初始化数据库
./bin/codemcp-db check     # 检查数据库连接
./bin/codemcp-db migrate   # 运行数据库迁移
./bin/codemcp-db downgrade # 回滚迁移
```

#### 4. 通用 CLI (codemcp)

通用命令行接口，无参数时自动启动交互式控制台：

```bash
./bin/codemcp              # 启动交互式控制台
./bin/codemcp monitor      # 监控模式
./bin/codemcp status       # 查看系统状态
./bin/codemcp config       # 配置管理
```

#### 5. 开发工具 (codemcp-dev)

开发相关工具：

```bash
./bin/codemcp-dev test     # 运行测试
./bin/codemcp-dev lint     # 代码检查
./bin/codemcp-dev format   # 代码格式化
./bin/codemcp-dev docs     # 构建文档
```

### 环境要求

确保已激活虚拟环境并安装依赖：

```bash
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

pip install -e .
```

### 权限设置

首次使用时，需要给脚本添加执行权限：

```bash
chmod +x bin/*
```

### 快捷方式

可以将 `bin/` 目录添加到 PATH 环境变量，以便在任何位置使用：

```bash
export PATH="$PATH:/path/to/codemcp/bin"
```

然后可以直接使用：
```bash
code_shell
codemcp-server
codemcp-db init
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

### 连接方式

CodeMCP 使用简化的 MCP 协议，通过 WebSocket 进行通信。连接时无需 API 密钥认证，仅需指定客户端类型。

#### 正确的连接方法

**WebSocket 连接端点：**
```
ws://localhost:8000/mcp/ws/{client_type}
```

其中 `client_type` 必须是以下之一：
- `planner` - 规划器客户端（负责创建计划）
- `executor` - 执行器客户端（负责执行任务）

**重要说明：**
- 连接 URL 必须包含正确的客户端类型（planner 或 executor）
- 不需要额外的认证参数
- 服务器必须在运行状态（默认端口 8000）

#### 启动服务器

在连接之前，确保 CodeMCP 服务器正在运行：

```bash
# 启动 Gateway 服务器（包含 MCP 端点）
codemcp-server

# 或使用 uvicorn 直接启动
uvicorn codemcp.api.server:app --host 0.0.0.0 --port 8000 --reload
```

#### 验证连接

连接前可以验证服务器状态：

```bash
# 检查 MCP 服务器信息
curl http://localhost:8000/mcp/info

# 检查健康状态
curl http://localhost:8000/mcp/health
```

### Planner 集成

Planner 是通过 MCP 协议与 CodeMCP 通信的外部 AI，负责创建执行计划。

#### 正确的连接示例

```python
import asyncio
import json
import websockets
from datetime import datetime

async def connect_planner():
    """连接 Planner 客户端示例"""
    
    # 正确的连接 URL
    ws_url = "ws://localhost:8000/mcp/ws/planner"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ 成功连接到 MCP Planner 服务器")
            
            # 发送 Ping 消息测试连接
            ping_message = {
                "message_id": "test-ping-001",
                "message_type": "ping",
                "source": "my-planner-client",
                "destination": "server",
                "timestamp": datetime.now().isoformat(),
                "priority": "normal",
                "metadata": {}
            }
            
            await websocket.send(json.dumps(ping_message))
            print("📤 发送 Ping 消息")
            
            # 接收响应
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 收到响应: {response_data}")
            
            return True
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

# 运行连接测试
asyncio.run(connect_planner())
```

#### 创建计划示例

```python
async def create_plan_example():
    """创建计划示例"""
    
    ws_url = "ws://localhost:8000/mcp/ws/planner"
    
    async with websockets.connect(ws_url) as websocket:
        # 创建计划消息
        plan_message = {
            "message_id": "plan-create-001",
            "message_type": "plan/create",
            "source": "planner-agent",
            "destination": "server",
            "timestamp": datetime.now().isoformat(),
            "priority": "normal",
            "metadata": {},
            "system_id": "1",
            "description": "用户认证模块开发",
            "plan_data": {
                "blocks": [
                    {
                        "name": "用户认证模块",
                        "features": [
                            {
                                "name": "用户注册",
                                "tests": [
                                    {
                                        "name": "注册API测试",
                                        "command": "pytest tests/test_auth.py::test_register"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        await websocket.send(json.dumps(plan_message))
        response = await websocket.recv()
        
        print(f"计划创建响应: {response}")
        return json.loads(response)
```

### Executor 集成

Executor 是执行具体测试任务的外部 agent，通过 MCP WebSocket 连接与服务器通信。

#### 正确的连接方法

**WebSocket 连接端点：**
```
ws://localhost:8000/mcp/ws/executor
```

#### 完整的 Executor 示例

```python
import asyncio
import json
import websockets
from datetime import datetime

class CodeMCPExecutor:
    """CodeMCP Executor 客户端"""
    
    def __init__(self, executor_id="executor-001"):
        self.executor_id = executor_id
        self.ws_url = "ws://localhost:8000/mcp/ws/executor"
        self.websocket = None
        
    async def connect(self):
        """连接到 MCP 服务器"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            print(f"✅ Executor {self.executor_id} 已连接到 MCP 服务器")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def fetch_task(self):
        """获取待执行的任务"""
        if not self.websocket:
            await self.connect()
            
        # 发送任务获取请求
        fetch_message = {
            "message_id": f"fetch-{datetime.now().timestamp()}",
            "message_type": "task/fetch",
            "source": self.executor_id,
            "destination": "server",
            "timestamp": datetime.now().isoformat(),
            "priority": "normal",
            "metadata": {},
            "executor_id": self.executor_id,
            "capabilities": ["python", "pytest", "shell"],
            "max_tasks": 1
        }
        
        await self.websocket.send(json.dumps(fetch_message))
        
        # 等待响应
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("message_type") == "error":
            print(f"⚠ 获取任务失败: {response_data.get('metadata', {}).get('error_message')}")
            return None
            
        # 解析任务数据
        task_data = response_data.get("metadata", {})
        if task_data.get("status") == "no_tasks":
            print("📭 暂无可用任务")
            return None
            
        print(f"📥 获取到任务: {task_data}")
        return task_data
    
    async def submit_result(self, task_id, success, output="", error_message="", duration=0.0):
        """提交任务执行结果"""
        result_message = {
            "message_id": f"result-{datetime.now().timestamp()}",
            "message_type": "task/result",
            "source": self.executor_id,
            "destination": "server",
            "timestamp": datetime.now().isoformat(),
            "priority": "normal",
            "metadata": {},
            "task_id": task_id,
            "exit_code": 0 if success else 1,
            "stdout": output,
            "stderr": error_message,
            "duration": duration,
            "success": success,
            "error_message": error_message if not success else None
        }
        
        await self.websocket.send(json.dumps(result_message))
        
        # 等待确认
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("message_type") == "error":
            print(f"⚠ 提交结果失败: {response_data.get('metadata', {}).get('error_message')}")
            return False
            
        print(f"✅ 任务结果提交成功: {task_id}")
        return True
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 连接已关闭")

# 使用示例
async def executor_example():
    executor = CodeMCPExecutor("my-executor-001")
    
    # 连接服务器
    if not await executor.connect():
        return
    
    try:
        # 获取任务
        task = await executor.fetch_task()
        
        if task:
            task_id = task.get("task_id")
            command = task.get("command", "")
            
            print(f"执行任务 {task_id}: {command}")
            
            # 模拟任务执行
            import subprocess
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # 提交结果
                success = result.returncode == 0
                await executor.submit_result(
                    task_id=task_id,
                    success=success,
                    output=result.stdout,
                    error_message=result.stderr,
                    duration=5.5
                )
                
            except subprocess.TimeoutExpired:
                await executor.submit_result(
                    task_id=task_id,
                    success=False,
                    error_message="任务执行超时",
                    duration=30.0
                )
                
    finally:
        await executor.close()

# 运行示例
asyncio.run(executor_example())
```

#### 备选方案：使用 HTTP API（如果启用）

如果 MCP 服务器的 HTTP 端点已启用，也可以使用以下方式：

```python
import httpx

async def fetch_task_http():
    """通过 HTTP 获取任务（如果端点启用）"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/mcp/executor/tasks")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"HTTP 请求失败: {e}")
            return None

async def submit_result_http(task_id, result_data):
    """通过 HTTP 提交结果（如果端点启用）"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://localhost:8000/mcp/executor/tasks/{task_id}/result",
                json=result_data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"HTTP 提交失败: {e}")
            return False
```

**注意：** 默认情况下，MCP 服务器的 HTTP 端点可能未完全实现，建议优先使用 WebSocket 连接。

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