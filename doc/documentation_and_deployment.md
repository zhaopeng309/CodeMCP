# 项目文档与部署指南

## 概述
本文档提供 CodeMCP 项目的完整文档和部署指南，包括安装、配置、使用和运维说明。

## 项目文档结构

### 文档目录
```
docs/
├── index.md                      # 项目首页
├── getting-started/              # 快速开始
│   ├── installation.md
│   ├── configuration.md
│   └── first-steps.md
├── user-guide/                   # 用户指南
│   ├── concepts.md              # 核心概念
│   ├── planner-guide.md         # Planner 使用指南
│   ├── executor-guide.md        # Executor 使用指南
│   └── console-guide.md         # Console 使用指南
├── api-reference/               # API 参考
│   ├── overview.md
│   ├── systems-api.md
│   ├── tasks-api.md
│   ├── queue-api.md
│   └── mcp-protocol.md
├── development/                 # 开发文档
│   ├── architecture.md
│   ├── database-schema.md
│   ├── testing.md
│   └── contributing.md
├── deployment/                  # 部署指南
│   ├── docker.md
│   ├── kubernetes.md
│   ├── monitoring.md
│   └── troubleshooting.md
└── examples/                    # 示例
    ├── basic-workflow.md
    ├── failure-recovery.md
    └── custom-integration.md
```

## 快速开始指南

### 1. 安装

#### 使用 pip 安装
```bash
# 安装核心包
pip install codemcp

# 安装开发版本
pip install git+https://github.com/zhaopeng309/CodeMCP.git

# 安装可选组件
pip install codemcp[dev]      # 开发工具
pip install codemcp[cli]      # CLI 工具
pip install codemcp[all]      # 所有组件
```

#### 使用 Docker
```bash
# 拉取镜像
docker pull yourusername/codemcp:latest

# 运行 Gateway 服务器
docker run -d \
  --name codemcp-gateway \
  -p 8000:8000 \
  -v ./data:/app/data \
  -e DATABASE_URL=sqlite:///data/codemcp.db \
  yourusername/codemcp:latest

# 运行 Console
docker run -it \
  --name codemcp-console \
  --network host \
  yourusername/codemcp:latest \
  codemcp interactive
```

### 2. 配置

#### 环境变量
```bash
# 数据库配置
export DATABASE_URL="sqlite:///./codemcp.db"
# export DATABASE_URL="postgresql://user:password@localhost/codemcp"

# 服务器配置
export HOST="0.0.0.0"
export PORT=8000
export DEBUG=false
export LOG_LEVEL="INFO"

# API 配置
export API_PREFIX="/api/v1"
export CORS_ORIGINS='["http://localhost:3000"]'

# 安全配置
export API_KEY="your-secret-api-key"
export JWT_SECRET="your-jwt-secret"

# 任务执行配置
export TASK_WINDOW_SIZE=5
export MAX_RETRIES=3
```

#### 配置文件
创建 `config.toml`:
```toml
[server]
host = "0.0.0.0"
port = 8000
debug = false
api_prefix = "/api/v1"

[database]
url = "sqlite:///./codemcp.db"
pool_size = 5
max_overflow = 10
echo = false

[security]
api_key = "your-secret-api-key"
jwt_secret = "your-jwt-secret"
cors_origins = ["http://localhost:3000"]

[task]
window_size = 5
max_retries = 3
default_priority = 0
max_duration = 300

[logging]
level = "INFO"
format = "json"
file = "/var/log/codemcp/server.log"

[monitoring]
enabled = true
prometheus_port = 9090
health_check_interval = 30
```

### 3. 初始化数据库
```bash
# 使用 Alembic 迁移
alembic upgrade head

# 或手动初始化
codemcp db init
```

### 4. 启动服务
```bash
# 启动 Gateway 服务器
codemcp-server

# 或使用 uvicorn 直接启动
uvicorn codemcp.api.server:app --host 0.0.0.0 --port 8000 --reload

# 启动交互式 Console
codemcp interactive

# 查看帮助
codemcp --help
```

## 用户指南

### 核心概念

#### 四层结构
1. **System (系统)**: 业务领域隔离，如"用户管理系统"
2. **Block (模块)**: 功能模块，如"数据库访问层"
3. **Feature (功能点)**: 具体功能，如"创建用户表"
4. **Test (测试)**: 验证单元，包含具体的测试命令

#### 工作流程
```
1. Planner 创建计划 → 2. Gateway 解析入库 → 3. 任务进入队列
4. Executor 获取任务 → 5. 执行代码修改 → 6. 运行测试
7. 测试通过 → 8. 任务完成 → 9. 更新状态
7. 测试失败 → 8. 重试或中止 → 9. Planner 重新规划
```

### Planner 使用指南

#### 创建计划
```python
import httpx
import json

# MCP 协议请求
plan_data = {
    "system_id": 1,
    "plan_name": "用户认证模块开发",
    "blocks": [
        {
            "name": "数据库层",
            "features": [
                {
                    "name": "创建用户表",
                    "test_command": "pytest tests/test_user_model.py"
                }
            ]
        }
    ]
}

response = httpx.post(
    "http://localhost:8000/mcp/planner/create_plan",
    json=plan_data,
    headers={"Authorization": "Bearer your-api-key"}
)

plan_id = response.json()["result"]["plan_id"]
```

#### 监控进度
```python
# 查询计划状态
response = httpx.post(
    "http://localhost:8000/mcp/planner/get_plan_status",
    json={"plan_id": plan_id}
)

status = response.json()["result"]
print(f"完成率: {status['completion_rate']*100:.1f}%")
```

### Executor 使用指南

#### 获取任务
```python
import asyncio
import httpx

async def fetch_task():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp/executor/get_next_task",
            json={
                "executor_id": "my-executor",
                "capabilities": ["python", "pytest"]
            }
        )
        
        task = response.json()["result"]
        return task

# 执行任务
task = asyncio.run(fetch_task())
print(f"任务: {task['feature_name']}")
print(f"测试命令: {task['test_command']}")
```

#### 提交结果
```python
async def submit_result(task_id, success, output):
    async with httpx.AsyncClient() as client:
        if success:
            response = await client.post(
                "http://localhost:8000/mcp/executor/complete_task",
                json={
                    "task_id": task_id,
                    "exit_code": 0,
                    "stdout": output,
                    "duration": 45.2
                }
            )
        else:
            response = await client.post(
                "http://localhost:8000/mcp/executor/fail_task",
                json={
                    "task_id": task_id,
                    "exit_code": 1,
                    "stderr": output,
                    "error_type": "TEST_FAILURE"
                }
            )
        
        return response.json()
```

### Console 使用指南

#### 交互式模式
```bash
# 启动全屏交互式控制台
codemcp interactive

# 使用命令行模式
codemcp monitor --follow
codemcp queue status
codemcp task list --status running
```

#### 快捷键参考
| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Q` | 退出 | 退出应用程序 |
| `H` | 帮助 | 显示快捷键帮助 |
| `R` | 刷新 | 手动刷新界面 |
| `F` | 跟随模式 | 切换自动滚动 |
| `TAB` | 切换面板 | 在面板间切换 |
| `P` | 暂停队列 | 暂停任务分发 |
| `U` | 恢复队列 | 恢复任务分发 |
| `S` | 选择系统 | 选择监控的系统 |
| `1-5` | 选择任务 | 选择任务进行操作 |

## API 参考

### 基础 URL
- Gateway API: `http://localhost:8000/api/v1`
- MCP 协议: `http://localhost:8000/mcp`
- WebSocket: `ws://localhost:8000/ws`

### 认证
所有 API 请求都需要在 Header 中包含 API Key:
```http
Authorization: Bearer your-api-key
X-MCP-Role: planner  # 或 executor
```

### 主要端点

#### 系统管理
```http
GET    /api/v1/systems           # 列出系统
POST   /api/v1/systems           # 创建系统
GET    /api/v1/systems/{id}      # 获取系统详情
PUT    /api/v1/systems/{id}      # 更新系统
DELETE /api/v1/systems/{id}      # 归档系统
```

#### 任务管理
```http
GET    /api/v1/tasks/next        # 获取下一个任务
POST   /api/v1/tasks/{id}/start  # 开始任务
POST   /api/v1/tasks/{id}/complete # 完成任务
POST   /api/v1/tasks/{id}/fail   # 标记任务失败
```

#### 队列管理
```http
GET    /api/v1/queue/status      # 队列状态
POST   /api/v1/queue/pause       # 暂停队列
POST   /api/v1/queue/resume      # 恢复队列
POST   /api/v1/queue/clear       # 清空队列
```

## 部署指南

### Docker 部署

#### Docker Compose 配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: codemcp
      POSTGRES_USER: codemcp
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U codemcp"]
      interval: 10s
      timeout: 5s
      retries: 5

  gateway:
    image: yourusername/codemcp:latest
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://codemcp:${DB_PASSWORD}@postgres/codemcp
      API_KEY: ${API_KEY}
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    command: ["codemcp-server"]
    restart: unless-stopped

  console:
    image: yourusername/codemcp:latest
    depends_on:
      - gateway
    environment:
      CODEMCP_SERVER_URL: http://gateway:8000
      CODEMCP_API_KEY: ${API_KEY}
    stdin_open: true
    tty: true
    command: ["codemcp", "interactive"]
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  grafana_data:
```

#### 启动服务
```bash
# 创建环境变量文件
cat > .env << EOF
DB_PASSWORD=your-db-password
API_KEY=your-api-key
GRAFANA_PASSWORD=grafana-admin
EOF

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f gateway

# 停止服务
docker-compose down
```

### Kubernetes 部署

#### Deployment 配置
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codemcp-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codemcp-gateway
  template:
    metadata:
      labels:
        app: codemcp-gateway
    spec:
      containers:
      - name: gateway
        image: yourusername/codemcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: codemcp-secrets
              key: database-url
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: codemcp-secrets
              key: api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: codemcp-gateway
spec:
  selector:
    app: codemcp-gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

#### 部署命令
```bash
# 创建命名空间
kubectl create namespace codemcp

# 创建密钥
kubectl create secret generic codemcp-secrets \
  --namespace codemcp \
  --from-literal=database-url=postgresql://user:pass@postgres/codemcp \
  --from-literal=api-key=your-api-key

# 部署应用
kubectl apply -f k8s/deployment.yaml -n codemcp

# 查看状态
kubectl get pods -n codemcp
kubectl get svc -n codemcp
```

## 监控与运维

### 健康检查
```bash
# 健康检查端点
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 详细状态
curl http://localhost:8000/api/v1/status
```

### 日志管理
```bash
# 查看 Gateway 日志
docker logs codemcp-gateway -f

# 查看结构化日志
tail -f /var/log/codemcp/server.log | jq .

# 日志轮转配置 (logrotate)
cat > /etc/logrotate.d/codemcp << EOF
/var/log/codemcp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 codemcp codemcp
    postrotate
        docker kill -s USR1 codemcp-gateway
    endscript
}
EOF
```

### 性能监控

#### Prometheus 配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'codemcp'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: '/metrics'
```

#### Grafana 仪表板
导入预配置的 Grafana 仪表板，监控以下指标：
- 任务执行速率
- 成功率/失败率
- 队列长度
- 窗口利用率
- 平均执行时间
- 系统资源使用率

### 备份与恢复

#### 数据库备份
```bash
# PostgreSQL 备份
pg_dump -U codemcp -h localhost codemcp > backup_$(date +%Y%m%d).sql

# SQLite 备份
cp /app/data/codemcp.db /backup/codemcp_$(date +%Y%m%d).db

# 自动备份脚本
cat > /usr/local/bin/backup_codemcp.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/codemcp"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
docker exec codemcp-postgres pg_dump -U codemcp codemcp > \
  $BACKUP_DIR/db_$DATE.sql

# 备份配置文件
tar czf $BACKUP_DIR/config_$DATE.tar.gz /app/config/

# 保留最近30天备份
find $BACKUP_DIR -type f -mtime +30 -delete
EOF
```

#### 恢复数据
```bash
# 恢复数据库
psql -U codemcp -h localhost codemcp < backup_20240101.sql

# 或使用 Docker
docker exec -i codemcp-postgres psql -U codemcp codemcp < backup.sql
```

## 故障