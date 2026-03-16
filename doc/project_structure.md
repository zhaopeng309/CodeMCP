# CodeMCP 项目结构规划

## 项目目录结构

```
codemcp/
├── src/
│   └── codemcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── models/                    # 数据模型层
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── system.py
│       │   ├── block.py
│       │   ├── feature.py
│       │   ├── test.py
│       │   └── task_queue.py
│       ├── database/                  # 数据库层
│       │   ├── __init__.py
│       │   ├── session.py
│       │   ├── engine.py
│       │   └── migrations/
│       │       ├── env.py
│       │       ├── script.py.mako
│       │       └── versions/
│       ├── api/                       # Gateway API
│       │   ├── __init__.py
│       │   ├── dependencies.py
│       │   ├── middleware.py
│       │   ├── server.py
│       │   ├── schemas/               # Pydantic 模型
│       │   │   ├── __init__.py
│       │   │   ├── system.py
│       │   │   ├── block.py
│       │   │   ├── feature.py
│       │   │   ├── task.py
│       │   │   └── common.py
│       │   └── routes/                # API 路由
│       │       ├── __init__.py
│       │       ├── systems.py
│       │       ├── blocks.py
│       │       ├── features.py
│       │       ├── tasks.py
│       │       ├── queue.py
│       │       ├── status.py
│       │       └── events.py
│       ├── core/                      # 核心业务逻辑
│       │   ├── __init__.py
│       │   ├── state_machine.py
│       │   ├── task_window.py
│       │   ├── executor.py
│       │   ├── planner.py
│       │   └── failure_handler.py
│       ├── cli/                       # Console CLI
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── ui/                    # 交互式界面
│       │   │   ├── __init__.py
│       │   │   ├── layout.py
│       │   │   ├── panels.py
│       │   │   ├── widgets.py
│       │   │   └── themes.py
│       │   └── commands/              # CLI 命令
│       │       ├── __init__.py
│       │       ├── monitor.py
│       │       ├── queue.py
│       │       ├── task.py
│       │       ├── system.py
│       │       ├── status.py
│       │       └── config.py
│       ├── mcp/                       # MCP 协议实现
│       │   ├── __init__.py
│       │   ├── protocol.py
│       │   ├── planner_client.py
│       │   ├── executor_client.py
│       │   └── server.py
│       └── utils/                     # 工具函数
│           ├── __init__.py
│           ├── logging.py
│           ├── validation.py
│           ├── serialization.py
│           └── time.py
├── tests/                            # 测试文件
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models/
│   ├── test_api/
│   ├── test_core/
│   ├── test_cli/
│   └── test_integration/
├── docs/                             # 文档
│   ├── index.md
│   ├── architecture.md
│   ├── api.md
│   ├── cli.md
│   └── deployment.md
├── scripts/                          # 脚本文件
│   ├── setup_db.py
│   ├── generate_docs.py
│   └── run_tests.sh
├── alembic.ini                       # Alembic 配置
├── .env.example                      # 环境变量示例
├── .gitignore
├── pyproject.toml                    # 项目配置
├── README.md
├── LICENSE
└── Dockerfile
```

## 配置文件说明

### 1. pyproject.toml (项目配置)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codemcp"
version = "0.1.0"
description = "CodeMCP - AI协同编排与执行服务器"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "prompt-toolkit>=3.0.0",
    "click>=8.0.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.25.0",
    "websockets>=12.0",
    "aiofiles>=23.0.0",
]

[project.scripts]
codemcp = "codemcp.cli.main:app"
codemcp-server = "codemcp.api.server:main"
```

### 2. .env.example (环境变量)
```bash
# 数据库配置
DATABASE_URL=sqlite:///./codemcp.db
# DATABASE_URL=postgresql://user:password@localhost/codemcp

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# API 配置
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# 任务执行配置
TASK_WINDOW_SIZE=5
MAX_RETRIES=3
DEFAULT_PRIORITY=0

# 日志配置
LOG_FILE=/var/log/codemcp/server.log
LOG_FORMAT=json
```

### 3. Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml ./

# 安装Python依赖
RUN pip install --no-cache-dir .[dev]

# 复制应用代码
COPY src/ ./src/
COPY alembic.ini ./
COPY .env ./

# 创建非root用户
RUN useradd -m -u 1000 codemcp && chown -R codemcp:codemcp /app
USER codemcp

# 数据库迁移
RUN alembic upgrade head

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "codemcp.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. alembic.ini (数据库迁移)
```ini
[alembic]
script_location = src/codemcp/database/migrations
sqlalchemy.url = sqlite:///./codemcp.db
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88 REVISION_SCRIPT_FILENAME

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

## 模块职责说明

### 1. models/ 数据模型
- 定义SQLAlchemy ORM模型
- 包含System、Block、Feature、Test四层结构
- 定义模型之间的关系和约束

### 2. database/ 数据库层
- 数据库连接和会话管理
- Alembic迁移配置
- 数据库工具函数

### 3. api/ Gateway API
- FastAPI应用和路由
- Pydantic请求/响应模型
- API认证和中间件
- WebSocket事件推送

### 4. core/ 核心逻辑
- 状态机实现
- 任务窗口化执行
- 失败处理和重试逻辑
- 执行器接口

### 5. cli/ Console CLI
- Typer CLI应用
- prompt-toolkit交互界面
- 命令实现
- 配置管理

### 6. mcp/ MCP协议
- MCP协议实现
- Planner和Executor客户端
- 协议消息处理

### 7. utils/ 工具函数
- 日志配置
- 数据验证
- 序列化工具
- 时间处理

## 开发工作流

### 1. 环境设置
```bash
# 克隆项目
git clone <repository>
cd codemcp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -e .[dev]

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件
```

### 2. 数据库初始化
```bash
# 创建数据库
alembic upgrade head

# 生成迁移（当模型变更时）
alembic revision --autogenerate -m "描述变更"
alembic upgrade head
```

### 3. 开发服务器
```bash
# 启动Gateway服务器
codemcp-server

# 启动交互式Console
codemcp

# 运行测试
pytest
```

### 4. 代码质量
```bash
# 代码格式化
black src/
isort src/

# 代码检查
ruff check src/
mypy src/

# 运行测试
pytest --cov=src/codemcp
```

## 下一步行动
1. 创建实际的Python包结构
2. 实现数据库模型
3. 配置Alembic迁移
4. 实现核心状态机逻辑
5. 开发CLI界面原型