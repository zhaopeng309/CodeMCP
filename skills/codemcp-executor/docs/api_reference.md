# API 参考

## 概述

CodeMCP Executor 通过 HTTP API 与 CodeMCP 服务器通信。本文档描述执行器使用的 API 接口。

## 基础信息

### 服务器地址
```
http://localhost:8000  # 默认地址
```

### 认证方式
```bash
# 使用 Bearer Token 认证
Authorization: Bearer your-api-key-here
```

### 通用响应格式
```json
{
  "status": "success",
  "data": {},
  "message": "操作成功",
  "timestamp": "2026-03-17T10:00:00Z"
}
```

### 错误响应格式
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "任务ID",
      "issue": "不能为空"
    }
  },
  "timestamp": "2026-03-17T10:00:00Z"
}
```

## 健康检查

### 检查服务器状态
```
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-17T10:00:00Z"
}
```

## 任务管理

### 获取下一个任务
```
GET /api/v1/tasks/next
```

**查询参数**:
- `executor_id` (可选): 执行器ID
- `type` (可选): 任务类型 (feature, bugfix, test, etc.)
- `priority` (可选): 优先级 (high, medium, low)

**响应示例** (成功):
```json
{
  "id": "TASK-001",
  "title": "实现用户登录功能",
  "type": "feature",
  "priority": "high",
  "description": "实现用户登录的API接口和前端页面...",
  "created_at": "2026-03-17T09:00:00Z",
  "created_by": "planner-001",
  "estimated_duration": "2小时",
  "commands": [
    {
      "command": "mkdir -p src/api src/frontend",
      "workdir": ".",
      "timeout": 30,
      "type": "setup"
    }
  ],
  "dependencies": ["fastapi", "pytest"],
  "tags": ["authentication", "api"],
  "success_criteria": ["所有测试通过", "代码符合规范"]
}
```

**响应示例** (无任务):
```json
{
  "status": "no_tasks",
  "message": "没有可用的任务",
  "timestamp": "2026-03-17T10:00:00Z"
}
```

### 更新任务状态
```
PUT /api/v1/tasks/{task_id}/status
```

**请求体**:
```json
{
  "status": "running",
  "message": "开始执行任务",
  "executor_id": "executor-001"
}
```

**状态值**:
- `pending`: 待处理
- `running`: 执行中
- `success`: 成功完成
- `failed`: 执行失败
- `cancelled`: 已取消

**响应示例**:
```json
{
  "status": "success",
  "message": "任务状态更新成功",
  "data": {
    "task_id": "TASK-001",
    "status": "running",
    "updated_at": "2026-03-17T10:05:00Z"
  }
}
```

### 提交任务结果
```
POST /api/v1/tasks/{task_id}/result
```

**请求体**:
```json
{
  "task_id": "TASK-001",
  "status": "success",
  "executor_id": "executor-001",
  "summary": "任务执行成功，所有测试通过",
  "timestamp": "2026-03-17T10:30:00Z",
  "execution_time": 125,
  "test_results": {
    "framework": "pytest",
    "total_tests": 5,
    "passed": 5,
    "failed": 0,
    "coverage": 92.5
  },
  "artifacts": ["src/api/login.py", "tests/test_login.py"],
  "metrics": {
    "code_lines": 150,
    "test_lines": 75
  },
  "error_summary": ""
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "任务结果提交成功",
  "data": {
    "task_id": "TASK-001",
    "result_id": "RESULT-001",
    "received_at": "2026-03-17T10:31:00Z"
  }
}
```

### 获取任务列表
```
GET /api/v1/tasks
```

**查询参数**:
- `status` (可选): 任务状态
- `executor_id` (可选): 执行器ID
- `limit` (可选): 返回数量限制 (默认: 10)
- `offset` (可选): 偏移量

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "id": "TASK-001",
        "title": "实现用户登录功能",
        "type": "feature",
        "status": "running",
        "priority": "high",
        "created_at": "2026-03-17T09:00:00Z",
        "assigned_to": "executor-001"
      }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}
```

## 执行器管理

### 注册执行器
```
POST /api/v1/executors/register
```

**请求体**:
```json
{
  "id": "executor-001",
  "name": "AI Code Executor",
  "role": "feature_implementation",
  "capabilities": ["python", "testing", "api"],
  "version": "1.0.0"
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "执行器注册成功",
  "data": {
    "executor_id": "executor-001",
    "registered_at": "2026-03-17T09:00:00Z",
    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 心跳检测
```
POST /api/v1/executors/{executor_id}/heartbeat
```

**请求体**:
```json
{
  "status": "active",
  "current_task": "TASK-001",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 120,
    "queue_size": 0
  }
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "心跳接收成功"
}
```

## 文件上传

### 上传任务产物
```
POST /api/v1/tasks/{task_id}/artifacts
```

**请求头**:
```
Content-Type: multipart/form-data
```

**表单字段**:
- `file`: 文件内容
- `name`: 文件名
- `type`: 文件类型 (code, log, report, etc.)

**响应示例**:
```json
{
  "status": "success",
  "message": "文件上传成功",
  "data": {
    "artifact_id": "ARTIFACT-001",
    "filename": "login.py",
    "size": 2048,
    "url": "/api/v1/artifacts/ARTIFACT-001"
  }
}
```

### 下载任务产物
```
GET /api/v1/artifacts/{artifact_id}
```

**响应**: 文件内容

## 错误代码

### 通用错误
| 错误代码 | 描述 | HTTP状态码 |
|---------|------|-----------|
| `VALIDATION_ERROR` | 请求参数验证失败 | 400 |
| `AUTH_REQUIRED` | 需要认证 | 401 |
| `FORBIDDEN` | 权限不足 | 403 |
| `NOT_FOUND` | 资源不存在 | 404 |
| `SERVER_ERROR` | 服务器内部错误 | 500 |

### 任务相关错误
| 错误代码 | 描述 | HTTP状态码 |
|---------|------|-----------|
| `TASK_NOT_FOUND` | 任务不存在 | 404 |
| `TASK_ALREADY_ASSIGNED` | 任务已被分配 | 409 |
| `TASK_STATUS_INVALID` | 任务状态无效 | 400 |
| `NO_TASKS_AVAILABLE` | 没有可用任务 | 404 |

### 执行器相关错误
| 错误代码 | 描述 | HTTP状态码 |
|---------|------|-----------|
| `EXECUTOR_NOT_FOUND` | 执行器不存在 | 404 |
| `EXECUTOR_INACTIVE` | 执行器未激活 | 400 |
| `CAPABILITY_MISMATCH` | 能力不匹配 | 400 |

## 使用示例

### 获取并执行任务的工作流
```bash
# 1. 获取下一个任务
curl -H "Authorization: Bearer $API_KEY" \
  "$SERVER_URL/api/v1/tasks/next?executor_id=$EXECUTOR_ID"

# 2. 更新任务状态为运行中
curl -X PUT -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status":"running","executor_id":"executor-001"}' \
  "$SERVER_URL/api/v1/tasks/TASK-001/status"

# 3. 执行任务...
# ... 任务执行代码 ...

# 4. 提交任务结果
curl -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @result.json \
  "$SERVER_URL/api/v1/tasks/TASK-001/result"
```

### 处理错误响应
```bash
# 示例：处理认证错误
response=$(curl -s -w "%{http_code}" -o response.json \
  -H "Authorization: Bearer $API_KEY" \
  "$SERVER_URL/api/v1/tasks/next")

if [[ "$response" == "401" ]]; then
    echo "认证失败，请检查API密钥"
    cat response.json | jq '.error.message'
fi
```

## 最佳实践

### 1. 错误处理
- 检查HTTP状态码
- 解析错误响应体
- 实现重试逻辑
- 记录详细错误信息

### 2. 连接管理
- 设置合理的超时时间
- 实现连接池
- 处理网络中断
- 定期检查连接状态

### 3. 认证安全
- 保护API密钥
- 使用HTTPS
- 定期更新令牌
- 实现令牌刷新机制

### 4. 性能优化
- 批量操作
- 缓存响应
- 压缩数据传输
- 异步处理

## 版本历史

### v1.0.0 (2026-03-17)
- 初始API版本
- 任务获取和状态更新
- 结果提交
- 执行器管理
- 文件上传