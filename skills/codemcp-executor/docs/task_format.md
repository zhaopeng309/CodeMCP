# 任务格式说明

## 概述

CodeMCP 任务是一个结构化的JSON对象，描述需要执行的工作单元。任务格式定义了执行器如何理解和执行工作。

## 基本结构

```json
{
  "id": "任务唯一标识符",
  "title": "任务标题",
  "type": "任务类型",
  "priority": "优先级",
  "description": "详细描述",
  "commands": [
    {
      "command": "要执行的命令",
      "workdir": "工作目录",
      "timeout": "超时时间",
      "type": "命令类型"
    }
  ],
  "dependencies": ["依赖项列表"],
  "tags": ["标签列表"],
  "success_criteria": ["成功标准"],
  "metadata": {
    "created_at": "创建时间",
    "created_by": "创建者",
    "estimated_duration": "预计耗时"
  }
}
```

## 字段详解

### 必需字段

| 字段名 | 类型 | 描述 | 示例 |
|--------|------|------|------|
| `id` | string | 任务唯一标识符 | `"TASK-001"`, `"feature-login-001"` |
| `title` | string | 任务标题，简洁描述 | `"实现用户登录功能"` |
| `type` | string | 任务类型 | `"feature"`, `"bugfix"`, `"test"` |
| `description` | string | 详细的任务描述 | `"实现用户登录的API接口和前端页面..."` |

### 可选字段

| 字段名 | 类型 | 描述 | 默认值 |
|--------|------|------|--------|
| `priority` | string | 任务优先级 | `"medium"` |
| `commands` | array | 要执行的命令列表 | `[]` |
| `dependencies` | array | 依赖项列表 | `[]` |
| `tags` | array | 标签列表 | `[]` |
| `success_criteria` | array | 成功标准列表 | `[]` |
| `metadata` | object | 元数据 | `{}` |
| `environment` | object | 环境要求 | `{}` |
| `resources` | object | 资源要求 | `{}` |

## 任务类型

### 预定义类型

| 类型 | 描述 | 典型用途 |
|------|------|----------|
| `feature` | 功能实现 | 开发新功能、模块 |
| `bugfix` | 缺陷修复 | 修复代码错误 |
| `test` | 测试相关 | 编写、运行测试 |
| `refactor` | 代码重构 | 优化代码结构 |
| `documentation` | 文档编写 | 编写技术文档 |
| `deployment` | 部署任务 | 部署应用程序 |
| `maintenance` | 维护任务 | 系统维护、更新 |
| `investigation` | 调查任务 | 问题分析、调研 |

### 自定义类型
可以定义项目特定的任务类型，建议使用前缀避免冲突：
- `project-feature`
- `team-bugfix`
- `infra-deployment`

## 优先级

### 预定义优先级
| 优先级 | 描述 | 执行顺序 |
|--------|------|----------|
| `critical` | 关键任务 | 最高 |
| `high` | 高优先级 | 高 |
| `medium` | 中优先级 | 中 (默认) |
| `low` | 低优先级 | 低 |
| `background` | 后台任务 | 最低 |

### 数字优先级
也可以使用数字表示优先级 (1-100):
- `1`: 最高优先级
- `50`: 中等优先级
- `100`: 最低优先级

## 命令格式

### 命令对象结构
```json
{
  "command": "要执行的shell命令",
  "workdir": "命令执行的工作目录",
  "timeout": 300,
  "type": "setup",
  "description": "命令描述",
  "expected_exit_code": 0,
  "retry_on_failure": true,
  "retry_count": 3,
  "retry_delay": 10,
  "ignore_failure": false
}
```

### 命令类型
| 类型 | 描述 | 示例 |
|------|------|------|
| `setup` | 环境设置 | 安装依赖、创建目录 |
| `coding` | 编码任务 | 编写代码、修改文件 |
| `testing` | 测试任务 | 运行测试、生成报告 |
| `build` | 构建任务 | 编译代码、打包应用 |
| `deploy` | 部署任务 | 部署到服务器 |
| `cleanup` | 清理任务 | 删除临时文件 |
| `verify` | 验证任务 | 检查结果、验证输出 |

### 命令执行规则
1. **顺序执行**: 命令按数组顺序执行
2. **工作目录**: 每个命令在指定的 `workdir` 中执行
3. **超时控制**: 命令执行超过 `timeout` 秒会被终止
4. **退出码检查**: 默认期望退出码为0
5. **重试机制**: 失败时根据配置重试
6. **失败处理**: 根据 `ignore_failure` 决定是否继续

## 依赖项

### 格式示例
```json
{
  "dependencies": [
    "fastapi>=0.95.0",
    "pytest>=7.0.0",
    "python>=3.9",
    "nodejs>=18.0.0",
    "docker",
    "git"
  ]
}
```

### 依赖类型
1. **Python包**: `package>=version`
2. **系统命令**: `command-name`
3. **环境要求**: `python>=3.9`, `nodejs>=18`
4. **服务依赖**: `postgresql`, `redis`
5. **文件依赖**: `file:///path/to/file`

## 成功标准

### 格式示例
```json
{
  "success_criteria": [
    "所有测试通过",
    "代码覆盖率 > 80%",
    "无编译警告",
    "API响应时间 < 100ms",
    "通过代码审查",
    "文档完整"
  ]
}
```

### 标准类型
1. **测试相关**: 测试通过、覆盖率达标
2. **代码质量**: 无警告、通过lint检查
3. **性能要求**: 响应时间、资源使用
4. **功能完整**: 所有需求实现
5. **文档要求**: 文档完整、示例可用

## 元数据

### 标准元数据字段
```json
{
  "metadata": {
    "created_at": "2026-03-17T09:00:00Z",
    "created_by": "planner-001",
    "estimated_duration": "2小时",
    "complexity": "medium",
    "risk_level": "low",
    "project": "用户管理系统",
    "module": "认证模块",
    "version": "1.0.0"
  }
}
```

### 自定义元数据
可以添加项目特定的元数据字段：
```json
{
  "metadata": {
    "jira_ticket": "PROJ-123",
    "sprint": "Sprint 5",
    "assignee": "developer@example.com",
    "reviewers": ["reviewer1", "reviewer2"]
  }
}
```

## 环境要求

### 格式示例
```json
{
  "environment": {
    "os": ["linux", "darwin"],
    "python": ">=3.9",
    "memory": "2GB",
    "disk": "10GB",
    "network": true,
    "gpu": false,
    "services": ["postgresql:5432", "redis:6379"]
  }
}
```

## 完整示例

### 功能实现任务
```json
{
  "id": "feature-login-001",
  "title": "实现用户登录功能",
  "type": "feature",
  "priority": "high",
  "description": "实现用户登录的API接口和前端页面，包括：\n1. 登录表单页面\n2. 登录API接口\n3. 身份验证逻辑\n4. 会话管理\n5. 错误处理机制",
  "commands": [
    {
      "command": "mkdir -p src/api/auth src/frontend/pages",
      "workdir": ".",
      "timeout": 30,
      "type": "setup",
      "description": "创建目录结构"
    },
    {
      "command": "pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt]",
      "workdir": ".",
      "timeout": 300,
      "type": "setup",
      "description": "安装Python依赖"
    },
    {
      "command": "echo 'from fastapi import FastAPI, Depends, HTTPException\\n# ... 完整的API代码 ...' > src/api/auth/login.py",
      "workdir": ".",
      "timeout": 120,
      "type": "coding",
      "description": "编写登录API代码"
    },
    {
      "command": "echo '<!DOCTYPE html>\\n<html>\\n<!-- 完整的前端代码 ... -->\\n</html>' > src/frontend/pages/login.html",
      "workdir": ".",
      "timeout": 120,
      "type": "coding",
      "description": "编写登录页面"
    },
    {
      "command": "echo 'import pytest\\nfrom fastapi.testclient import TestClient\\n# ... 完整的测试代码 ...' > tests/test_login.py",
      "workdir": ".",
      "timeout": 90,
      "type": "testing",
      "description": "编写测试用例"
    },
    {
      "command": "python -m pytest tests/test_login.py -v --cov=src/api/auth --cov-report=html",
      "workdir": ".",
      "timeout": 180,
      "type": "testing",
      "description": "运行测试并生成覆盖率报告",
      "expected_exit_code": 0,
      "retry_on_failure": true,
      "retry_count": 2
    }
  ],
  "dependencies": [
    "fastapi>=0.95.0",
    "uvicorn>=0.21.0",
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "python>=3.9",
    "git"
  ],
  "tags": ["authentication", "api", "frontend", "security"],
  "success_criteria": [
    "所有测试通过",
    "代码覆盖率 > 85%",
    "API响应时间 < 50ms",
    "无安全漏洞",
    "文档完整"
  ],
  "metadata": {
    "created_at": "2026-03-17T09:00:00Z",
    "created_by": "planner-001",
    "estimated_duration": "3小时",
    "complexity": "medium",
    "risk_level": "medium",
    "project": "用户管理系统",
    "module": "认证模块"
  },
  "environment": {
    "os": ["linux", "darwin"],
    "python": ">=3.9",
    "memory": "1GB",
    "services": []
  }
}
```

### 测试任务
```json
{
  "id": "test-coverage-001",
  "title": "运行测试并生成覆盖率报告",
  "type": "test",
  "priority": "medium",
  "description": "运行项目的所有测试，生成测试报告和覆盖率报告",
  "commands": [
    {
      "command": "python -m pytest tests/ -v --cov=src --cov-report=term --cov-report=html:coverage_html",
      "workdir": ".",
      "timeout": 600,
      "type": "testing",
      "description": "运行测试并生成覆盖率报告"
    },
    {
      "command": "python -m coverage json -o coverage.json",
      "workdir": ".",
      "timeout": 30,
      "type": "testing",
      "description": "生成JSON格式的覆盖率数据"
    }
  ],
  "success_criteria": [
    "所有测试通过",
    "总体覆盖率 > 80%",
    "关键模块覆盖率 > 90%",
    "无测试失败"
  ],
  "metadata": {
    "created_at": "2026-03-17T10:00:00Z",
    "created_by": "qa-001"
  }
}
```

## 验证规则

### 必需字段验证
1. `id`: 非空字符串，长度1-100字符
2. `title`: 非空字符串，长度1-200字符
3. `type`: 必须为预定义类型或有效的自定义类型
4. `description`: 非空字符串，长度1-5000字符

### 命令验证
1. 每个命令必须包含 `command` 字段
2. `timeout` 必须为正整数
3. `workdir` 必须是有效路径格式
4. `type` 必须为预定义类型

### 数据验证
1. 优先级必须为有效值
2. 依赖项必须是字符串数组
3. 标签必须是字符串数组
4. 成功标准必须是字符串数组

## 扩展机制

### 自定义字段
可以在任务中添加自定义字段，建议使用命名空间避免冲突：
```json
{
  "custom_fields": {
    "company:project_id": "PROJ-123",
    "team:sprint": "Sprint 5",
    "internal:reviewer": "alice@example.com"
  }
}
```

### 钩子脚本
可以通过命令实现自定义钩子：
```json
{
  "hooks": {
    "pre_execute": "scripts/pre-task.sh",
    "post_success": "scripts/post-success.sh",
    "post_failure": "scripts/post-failure.sh"
  }
}
```

## 最佳实践

### 任务设计
1. **单一职责**: 每个任务只做一件事
2. **适当粒度**: 任务不宜过大或过小
3. **明确标准**: 清晰定义成功标准
4. **充分描述**: 提供足够的信息供执行器理解

### 命令设计
1. **幂等性**: 命令可以安全重试
2. **进度输出**: 命令应提供进度信息
3. **错误处理**: 命令应返回有意义的退出码
4. **资源清理**: 命令应清理临时资源

### 依赖管理
1. **明确版本**: 指定依赖的版本范围
2. **最小依赖**: 只包含必要的依赖
3. **环境兼容**: 考虑不同环境的兼容性
4. **依赖检查**: 在任务开始时检查依赖