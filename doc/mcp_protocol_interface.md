# Planner 与 Executor 的 MCP 协议接口

## 概述
MCP（Model Context Protocol）是 CodeMCP 系统中 Planner 和 Executor 与 Gateway 通信的核心协议。本文档定义 MCP 协议的接口规范、消息格式和通信流程。

## MCP 协议架构

### 协议层
```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Protocol Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Transport Layer (HTTP/WebSocket)                           │
│  Message Format (JSON-RPC 2.0)                              │
│  Authentication & Authorization                             │
│  Error Handling & Retry Logic                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │   Role-Specific     │
            │     Interfaces      │
            ├─────────────────────┤
            │  Planner Interface  │
            │  Executor Interface │
            └─────────────────────┘
```

### 通信模式
1. **请求-响应模式**: 基于 HTTP 的同步通信
2. **事件推送模式**: 基于 WebSocket 的异步通信
3. **长轮询模式**: 用于任务获取和状态更新

## 基础协议规范

### 消息格式 (JSON-RPC 2.0)
```json
{
  "jsonrpc": "2.0",
  "id": "request-123",
  "method": "method_name",
  "params": {
    // 方法参数
  }
}
```

### 响应格式
```json
{
  "jsonrpc": "2.0",
  "id": "request-123",
  "result": {
    // 成功结果
  }
}
```

### 错误格式
```json
{
  "jsonrpc": "2.0",
  "id": "request-123",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "details": "Additional error information"
    }
  }
}
```

## 认证与授权

### API 密钥认证
```python
# 请求头
headers = {
    "Authorization": "Bearer {api_key}",
    "X-MCP-Role": "planner",  # 或 "executor"
    "X-MCP-Version": "1.0",
}
```

### 角色权限
| 角色 | 权限 |
|------|------|
| Planner | 创建计划、查询状态、重新规划 |
| Executor | 获取任务、提交结果、查询任务详情 |

## Planner 接口

### 1. 计划管理

#### `mcp.planner.create_plan`
创建新的开发计划

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "plan-create-001",
  "method": "mcp.planner.create_plan",
  "params": {
    "system_id": 1,
    "plan_name": "用户认证模块开发",
    "plan_version": "1.0",
    "blocks": [
      {
        "name": "数据库层",
        "description": "用户表和数据访问",
        "priority": 0,
        "features": [
          {
            "name": "创建用户表",
            "description": "设计并创建 users 表",
            "test_command": "pytest tests/test_user_model.py",
            "priority": 0
          }
        ]
      }
    ],
    "metadata": {
      "created_by": "planner-agent-001",
      "git_repo": "https://github.com/zhaopeng309/CodeMCP",
      "git_branch": "main"
    }
  }
}
```

**响应**:
```json
{
  "jsonrpc": "2.0",
  "id": "plan-create-001",
  "result": {
    "plan_id": "plan_123456",
    "system_id": 1,
    "blocks_created": 1,
    "features_created": 1,
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### `mcp.planner.update_plan`
更新计划（重新规划）

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "plan-update-001",
  "method": "mcp.planner.update_plan",
  "params": {
    "plan_id": "plan_123456",
    "reason": "测试失败，需要细化任务",
    "new_blocks": [
      {
        "name": "数据库层-细化",
        "description": "细化的数据库任务",
        "parent_block_id": 1,
        "features": [
          {
            "name": "创建用户表-结构",
            "description": "设计表结构",
            "test_command": "pytest tests/test_user_structure.py",
            "priority": 0
          }
        ]
      }
    ]
  }
}
```

### 2. 状态查询

#### `mcp.planner.get_plan_status`
获取计划状态

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "status-001",
  "method": "mcp.planner.get_plan_status",
  "params": {
    "plan_id": "plan_123456"
  }
}
```

**响应**:
```json
{
  "jsonrpc": "2.0",
  "id": "status-001",
  "result": {
    "plan_id": "plan_123456",
    "status": "in_progress",
    "completion_rate": 0.4,
    "blocks": [
      {
        "id": 1,
        "name": "数据库层",
        "status": "completed",
        "features": [
          {
            "id": 1,
            "name": "创建用户表",
            "status": "passed",
            "duration": 45.2,
            "last_test_result": {
              "exit_code": 0,
              "duration": 12.3
            }
          }
        ]
      }
    ],
    "failed_features": [],
    "next_checkpoint": "2024-01-01T12:00:00Z"
  }
}
```

#### `mcp.planner.get_failure_details`
获取失败详情

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "failure-001",
  "method": "mcp.planner.get_failure_details",
  "params": {
    "feature_id": 101,
    "include_logs": true
  }
}
```

### 3. 重新规划

#### `mcp.planner.analyze_failure`
分析失败原因

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "analyze-001",
  "method": "mcp.planner.analyze_failure",
  "params": {
    "feature_id": 101,
    "include_suggestions": true
  }
}
```

**响应**:
```json
{
  "jsonrpc": "2.0",
  "id": "analyze-001",
  "result": {
    "root_cause": "数据库连接失败",
    "error_type": "CONNECTION_ERROR",
    "suggested_fixes": [
      "检查数据库服务状态",
      "验证连接字符串",
      "增加连接超时时间"
    ],
    "recommended_actions": [
      {
        "type": "retry",
        "config": {
          "max_retries": 2,
          "backoff_seconds": 5
        }
      },
      {
        "type": "split_task",
        "tasks": [
          "先测试数据库连接",
          "再执行数据操作"
        ]
      }
    ]
  }
}
```

## Executor 接口

### 1. 任务获取

#### `mcp.executor.get_next_task`
获取下一个待执行任务

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "task-get-001",
  "method": "mcp.executor.get_next_task",
  "params": {
    "executor_id": "executor-001",
    "capabilities": ["python", "pytest", "git"],
    "preferences": {
      "max_duration": 300,
      "preferred_languages": ["python"]
    }
  }
}
```

**响应**:
```json
{
  "jsonrpc": "2.0",
  "id": "task-get-001",
  "result": {
    "task_id": "task_789",
    "feature_id": 101,
    "feature_name": "创建用户表",
    "block_name": "数据库层",
    "system_name": "用户管理系统",
    "test_command": "pytest tests/test_user_model.py",
    "code_context": {
      "git_repo": "https://github.com/zhaopeng309/CodeMCP",
      "git_branch": "main",
      "git_commit": "abc123",
      "file_paths": ["src/models/user.py", "tests/test_user_model.py"]
    },
    "requirements": {
      "dependencies": ["sqlalchemy", "pytest"],
      "environment": "python3.9",
      "timeout_seconds": 120
    },
    "metadata": {
      "priority": 0,
      "estimated_duration": 60,
      "retry_count": 0
    }
  }
}
```

#### `mcp.executor.reserve_task`
预留任务（窗口化机制）

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "reserve-001",
  "method": "mcp.executor.reserve_task",
  "params": {
    "executor_id": "executor-001",
    "feature_id": 101,
    "reservation_timeout": 300
  }
}
```

### 2. 任务执行

#### `mcp.executor.start_task`
开始执行任务

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "start-001",
  "method": "mcp.executor.start_task",
  "params": {
    "task_id": "task_789",
    "executor_id": "executor-001",
    "started_at": "2024-01-01T10:00:00Z"
  }
}
```

#### `mcp.executor.update_progress`
更新任务进度

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "progress-001",
  "method": "mcp.executor.update_progress",
  "params": {
    "task_id": "task_789",
    "progress": 0.5,
    "status": "running",
    "current_step": "运行测试套件",
    "estimated_remaining": 30
  }
}
```

### 3. 任务完成

#### `mcp.executor.complete_task`
完成任务（成功）

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "complete-001",
  "method": "mcp.executor.complete_task",
  "params": {
    "task_id": "task_789",
    "exit_code": 0,
    "stdout": "测试通过：10 passed, 0 failed",
    "stderr": "",
    "duration": 45.2,
    "artifacts": [
      {
        "type": "code_change",
        "file": "src/models/user.py",
        "diff": "+class User:\n+    id = Column(Integer, primary_key=True)"
      },
      {
        "type": "test_report",
        "file": "test_report.json",
        "content": "{\"passed\": 10, \"failed\": 0}"
      }
    ],
    "metadata": {
      "git_commit": "def456",
      "environment": "python3.9",
      "dependencies_installed": ["sqlalchemy==1.4.0"]
    }
  }
}
```

#### `mcp.executor.fail_task`
标记任务失败

**请求**:
```json
{
  "jsonrpc": "2.0",
  "id": "fail-001",
  "method": "mcp.executor.fail_task",
  "params": {
    "task_id": "task_789",
    "exit_code": 1,
    "stdout": "测试失败：8 passed, 2 failed",
    "stderr": "AssertionError: 预期用户ID为整数",
    "duration": 38.7,
    "error_type": "TEST_FAILURE",
    "error_details": {
      "failed_tests": ["test_user_creation", "test_user_update"],
      "error_traceback": "Traceback (most recent call last):\n...",
      "suggested_fix": "检查用户ID类型转换"
    },
    "can_retry": true,
    "suggested_retry_config": {
      "delay_seconds": 10,
      "additional_dependencies": []
    }
  }
}
```

## WebSocket 事件接口

### 连接建立
```
ws://localhost:8000/mcp/ws?role=planner&api_key=xxx
```

### 事件订阅
```json
{
  "jsonrpc": "2.0",
  "id": "subscribe-001",
  "method": "mcp.events.subscribe",
  "params": {
    "event_types": ["task_started", "task_completed", "task_failed"],
    "filters": {
      "system_id": 1,
      "plan_id": "plan_123456"
    }
  }
}
```

### 事件推送
```json
{
  "jsonrpc": "2.0",
  "method": "mcp.events.task_started",
  "params": {
    "event_id": "evt_001",
    "timestamp": "2024-01-01T10:00:00Z",
    "data": {
      "task_id": "task_789",
      "feature_id": 101,
      "feature_name": "创建用户表",
      "executor_id": "executor-001",
      "estimated_duration": 60
    }
  }
}
```

### 事件类型
| 事件类型 | 触发条件 | 数据内容 |
|----------|----------|----------|
| `task_started` | 任务开始执行 | 任务信息、执行者 |
| `task_completed` | 任务成功完成 | 结果、时长、产出物 |
| `task_failed` | 任务失败 | 错误信息、诊断数据 |
| `plan_created` | 新计划创建 | 计划详情 |
| `plan_updated` | 计划更新 | 更新内容、原因 |
| `block_aborted` | 模块中止 | 中止原因、影响范围 |
| `queue_paused` | 队列暂停 | 暂停原因、操作者 |
| `queue_resumed` | 队列恢复 | 恢复时间 |

## 错误处理

### 错误码定义
| 错误码 | 含义 | 建议操作 |
|--------|------|----------|
| `-32600` | 无效请求 | 检查请求格式 |
| `-32601` | 方法不存在 | 检查方法名 |
| `-32602` | 无效参数 | 检查参数格式 |
| `-32603` | 内部错误 | 联系管理员 |
| `-32000` | 服务器错误 | 重试或联系支持 |
| `-32001` | 未授权 | 检查API密钥 |
| `-32002` | 权限不足 | 检查角色权限 |
| `-32003` | 资源不存在 | 检查资源ID |
| `-32004` | 资源冲突 | 检查资源状态 |
| `-32005` | 窗口已满 | 等待窗口空闲 |
| `-32006` | 队列已暂停 | 等待队列恢复 |

### 重试策略
```python
class MCPRetryPolicy:
    """MCP 重试策略"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # 秒
        self.max_delay = 30.0  # 秒
        self.retryable_errors = [
            -32603,  # 内部错误
            -32000,  # 服务器错误
            429,     # 速率限制
            502,     # 网关错误
            503,     # 服务不可用
            504,     # 网关超时
        ]
    
    def should_retry(self, error_code: int) -> bool:
        """检查是否应该重试"""
        return error_code in self.retryable_errors
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)
```

## 客户端实现示例

### Planner 客户端
```python
# src/codemcp/mcp/planner_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

from ..utils.logging import get_logger


@dataclass
class MCPClientConfig:
    """MCP 客户端配置"""
    server_url: str
    api_key: str
    role: str = "planner"
    timeout: int = 30
    max_retries: int = 3


class PlannerClient:
    """Planner MCP 客户端"""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.client = httpx.AsyncClient(
            base_url=config.server_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "X-MCP-Role": config.role,
                "X-MCP-Version": "1.0",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )
        self