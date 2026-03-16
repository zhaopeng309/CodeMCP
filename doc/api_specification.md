# Gateway REST API 接口规范

## 概述
Gateway 是 CodeMCP 的通信中枢，基于 FastAPI 实现，提供完整的 RESTful API 接口。所有接口都遵循 OpenAPI 3.0 规范。

## 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **认证**: 目前为无认证（可扩展 API Key 或 JWT）

## 响应格式
所有 API 响应都遵循以下格式：
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "message": "操作成功"
}
```

错误响应：
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {...}
  },
  "message": "请求参数验证失败"
}
```

## API 端点

### 1. 系统管理

#### GET `/systems`
获取所有系统列表

**参数**:
- `status` (可选): 过滤状态，如 `active`, `archived`
- `limit` (可选): 每页数量，默认 20
- `offset` (可选): 偏移量，默认 0

**响应**:
```json
{
  "success": true,
  "data": {
    "systems": [
      {
        "id": 1,
        "name": "用户管理系统",
        "description": "管理用户认证和权限",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "stats": {
          "total_blocks": 5,
          "completed_blocks": 2,
          "total_features": 25,
          "completed_features": 10
        }
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

#### POST `/systems`
创建新系统

**请求体**:
```json
{
  "name": "订单管理系统",
  "description": "处理订单创建、支付和物流"
}
```

#### GET `/systems/{system_id}`
获取系统详情

#### PUT `/systems/{system_id}`
更新系统信息

#### DELETE `/systems/{system_id}`
归档系统（软删除）

### 2. 计划管理

#### POST `/plans`
导入计划（Plan 1.0 JSON）

**请求体**:
```json
{
  "system_id": 1,
  "plan": {
    "name": "用户认证模块开发",
    "blocks": [
      {
        "name": "数据库层",
        "description": "用户表和数据访问",
        "features": [
          {
            "name": "创建用户表",
            "description": "设计并创建 users 表",
            "test_command": "pytest tests/test_user_model.py"
          },
          {
            "name": "用户CRUD操作",
            "description": "实现用户的增删改查",
            "test_command": "pytest tests/test_user_crud.py"
          }
        ]
      },
      {
        "name": "API层",
        "description": "RESTful API 接口",
        "features": [
          {
            "name": "用户注册接口",
            "description": "POST /api/users/register",
            "test_command": "pytest tests/test_register_api.py"
          }
        ]
      }
    ]
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "plan_id": "plan_123",
    "system_id": 1,
    "blocks_created": 2,
    "features_created": 3,
    "message": "计划导入成功"
  }
}
```

### 3. 任务执行

#### GET `/tasks/next`
获取下一个待执行任务（窗口化机制）

**参数**:
- `system_id` (可选): 指定系统
- `limit` (可选): 获取数量，默认 1

**响应**:
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": 101,
        "feature_id": 1,
        "feature_name": "创建用户表",
        "block_name": "数据库层",
        "system_name": "用户管理系统",
        "test_command": "pytest tests/test_user_model.py",
        "priority": 0,
        "estimated_duration": 120
      }
    ],
    "window_used": 1,
    "window_capacity": 5
  }
}
```

#### POST `/tasks/{task_id}/start`
开始执行任务

**请求体**:
```json
{
  "executor_id": "executor_001",
  "started_at": "2024-01-01T10:00:00Z"
}
```

#### POST `/tasks/{task_id}/complete`
完成任务（测试通过）

**请求体**:
```json
{
  "exit_code": 0,
  "stdout": "测试通过：10 passed, 0 failed",
  "stderr": "",
  "duration": 45.2,
  "completed_at": "2024-01-01T10:01:00Z"
}
```

#### POST `/tasks/{task_id}/fail`
标记任务失败

**请求体**:
```json
{
  "exit_code": 1,
  "stdout": "测试失败：8 passed, 2 failed",
  "stderr": "AssertionError: 预期用户ID为整数",
  "duration": 38.7,
  "completed_at": "2024-01-01T10:01:30Z",
  "error_type": "TEST_FAILURE"
}
```

### 4. 队列管理

#### GET `/queue/status`
获取队列状态

**响应**:
```json
{
  "success": true,
  "data": {
    "window_capacity": 5,
    "window_used": 2,
    "pending_count": 15,
    "processing_count": 2,
    "completed_today": 8,
    "failed_today": 1,
    "is_paused": false,
    "paused_since": null
  }
}
```

#### POST `/queue/pause`
暂停任务分发

**响应**:
```json
{
  "success": true,
  "data": {
    "paused": true,
    "message": "队列已暂停"
  }
}
```

#### POST `/queue/resume`
恢复任务分发

#### POST `/queue/clear`
清空待处理队列

**参数**:
- `system_id` (可选): 只清空指定系统的队列
- `block_id` (可选): 只清空指定模块的队列

### 5. 状态监控

#### GET `/status`
获取系统整体状态

**响应**:
```json
{
  "success": true,
  "data": {
    "systems": [
      {
        "id": 1,
        "name": "用户管理系统",
        "completion_rate": 0.4,
        "block_stats": {
          "total": 5,
          "completed": 2,
          "in_progress": 1,
          "pending": 2
        },
        "feature_stats": {
          "total": 25,
          "passed": 10,
          "failed": 2,
          "running": 1,
          "pending": 12
        }
      }
    ],
    "global_stats": {
      "total_tasks": 150,
      "completed_tasks": 75,
      "failed_tasks": 10,
      "success_rate": 0.88,
      "avg_duration": 56.3
    }
  }
}
```

#### GET `/events`
获取最近事件（WebSocket 或 Server-Sent Events）

**参数**:
- `since` (可选): 时间戳，获取此时间之后的事件
- `types` (可选): 事件类型过滤，如 `task_started,task_completed`

**响应** (SSE 格式):
```
event: task_started
data: {"task_id": 101, "feature_name": "创建用户表", "timestamp": "2024-01-01T10:00:00Z"}

event: task_completed
data: {"task_id": 101, "success": true, "duration": 45.2, "timestamp": "2024-01-01T10:01:00Z"}
```

### 6. 失败处理

#### POST `/failures/{block_id}/abort`
中止整个模块（当测试失败时）

**请求体**:
```json
{
  "reason": "测试连续失败，需要重新规划",
  "error_details": {
    "failed_tests": [201, 202],
    "common_error": "数据库连接失败"
  }
}
```

#### GET `/failures/recent`
获取最近的失败记录

### 7. 统计报表

#### GET `/reports/completion`
生成完成率报表

**参数**:
- `system_id` (可选): 系统ID
- `start_date` (可选): 开始日期
- `end_date` (可选): 结束日期

#### GET `/reports/performance`
性能统计报表

## 错误码定义

| 错误码 | HTTP 状态码 | 描述 |
|--------|-------------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突（如重复名称） |
| `QUEUE_PAUSED` | 423 | 队列已暂停 |
| `WINDOW_FULL` | 429 | 执行窗口已满 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

## 速率限制
- 默认限制：100 请求/分钟
- 任务获取接口：10 请求/分钟
- 状态查询接口：无限制

## WebSocket 接口
```
ws://localhost:8000/ws/events
```

**消息类型**:
- `subscribe`: 订阅事件类型
- `unsubscribe`: 取消订阅
- `ping/pong`: 心跳检测

**事件类型**:
- `task_started`: 任务开始
- `task_completed`: 任务完成
- `task_failed`: 任务失败
- `queue_paused`: 队列暂停
- `queue_resumed`: 队列恢复
- `block_aborted`: 模块中止

## 下一步
1. 设计具体的请求/响应模型（Pydantic）
2. 定义 API 认证机制
3. 设计 API 文档（OpenAPI/Swagger）
4. 实现 API 版本管理策略