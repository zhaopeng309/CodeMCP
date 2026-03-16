---
name: codemcp-planner
description: "CodeMCP Planner Skill - 为CodeMCP AI协同编排服务器创建和管理开发计划，支持完整的开发工作流：创建计划 → 发送任务流 → 监听完成 → 自动git提交。使用场景：需要为软件开发项目创建结构化计划、分解任务、协调AI agent协同工作、管理四层数据模型(System→Block→Feature→Test)、自动版本控制。触发条件：用户提到'创建开发计划'、'项目规划'、'任务分解'、'CodeMCP计划'、'AI协同开发'、'自动git提交'、'任务流管理'等。"
metadata:
  {
    "openclaw": { 
      "emoji": "📋", 
      "requires": { 
        "anyBins": ["python", "curl", "websocat", "git"],
        "anyFiles": ["/home/designer/tools/CodeMCP/doc/plan_template.md"]
      },
      "recommends": {
        "skills": ["coding-agent"]
      }
    }
  }
---

# CodeMCP Planner Skill

## 🚀 快速开始

### 核心功能
1. **需求分析** - 将自然语言需求转换为结构化计划
2. **创建结构化计划** - 基于四层数据模型(System→Block→Feature→Test)
3. **发送任务流** - 向CodeMCP发送完整的开发任务序列
4. **自动git提交** - 监听feature完成事件，自动提交代码到Git仓库
5. **任务失败处理** - 监控任务状态，失败时重新规划并细化功能颗粒度
6. **用户反馈** - 实时通知用户执行状态和结果
7. **完整工作流** - 端到端的AI协同开发管理

### 一分钟示例
```python
from codemcp_planner import CodeMCPPlannerClient

# 创建客户端
client = CodeMCPPlannerClient()

# 连接到CodeMCP
websocket = await client.connect()

# 创建计划
plan_response = await client.create_plan(
    websocket,
    system_name="我的项目",
    description="项目描述",
    blocks=[...]  # 模块列表
)

# 发送任务流
await client.send_task_flow(
    websocket,
    plan_id=plan_response["data"]["plan_id"],
    tasks=[...]  # 任务列表
)

# 监听完成并自动git提交
await client.monitor_and_commit(
    websocket,
    plan_id=plan_response["data"]["plan_id"],
    repo_path="/path/to/repo",
    git_config={
        "user_name": "AI Developer",
        "user_email": "ai@example.com",
        "remote_url": "https://github.com/your/repo.git",
        "branch": "main"
    }
)
```

## 概述

CodeMCP Planner Skill 允许你作为规划器(Planner)连接到 CodeMCP AI协同编排服务器，为软件开发项目创建、管理和执行结构化计划。基于 CodeMCP 的四层数据模型：System → Block → Feature → Test。

## 核心概念

### 四层数据模型
1. **System（系统）**: 最高级别的业务领域或项目实例
2. **Block（模块）**: 属于 System 的功能模块
3. **Feature（功能）**: 具体的功能点，属于 Block
4. **Test（测试）**: 物理验证单元，属于 Feature

### Planner 角色
- 负责创建执行计划
- 分解复杂任务为可执行的测试单元
- 通过 MCP 协议与 CodeMCP Gateway 通信
- 协调多个 AI agent 协同工作

## 前置条件

### 1. 确保 CodeMCP 服务器运行
```bash
# 检查服务器状态
curl http://localhost:8000/mcp/health

# 如果未运行，启动服务器
cd /home/designer/tools/CodeMCP && ./start.sh --server --dev
```

### 2. 验证连接
```bash
# 检查 MCP 服务器信息
curl http://localhost:8000/mcp/info

# 应该返回类似：
# {
#   "service": "CodeMCP MCP Server",
#   "version": "1.0",
#   "protocol": "MCP (Model Context Protocol)",
#   "authentication": "none (simplified)",
#   "endpoints": { ... }
# }
```

## 基本工作流程

### 1. 连接 CodeMCP 服务器
```python
import asyncio
import json
import websockets

async def connect_planner():
    """连接到 CodeMCP Planner 端点"""
    ws_url = "ws://localhost:8000/mcp/ws/planner"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ 成功连接到 CodeMCP Planner 服务器")
            return websocket
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None
```

### 2. 创建项目计划
使用 CodeMCP 计划模板创建结构化计划：

```python
from datetime import datetime
import uuid

def create_plan_message(system_name, description, blocks):
    """创建计划消息"""
    return {
        "message_id": f"plan-{uuid.uuid4().hex[:8]}",
        "message_type": "plan_create",
        "source": "openclaw-planner",
        "destination": "server",
        "timestamp": datetime.now().isoformat(),
        "priority": "normal",
        "metadata": {},
        "data": {
            "system_name": system_name,
            "description": description,
            "blocks": blocks
        }
    }
```

### 3. 发送计划到服务器
```python
async def send_plan(websocket, plan_message):
    """发送计划到 CodeMCP 服务器"""
    await websocket.send(json.dumps(plan_message))
    
    # 等待响应
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        response_data = json.loads(response)
        return response_data
    except asyncio.TimeoutError:
        print("⚠️ 计划创建响应超时")
        return None
```

## 完整示例

### 示例：创建用户认证系统计划
```python
import asyncio
import json
import websockets
from datetime import datetime
import uuid

async def create_auth_system_plan():
    """创建用户认证系统计划"""
    
    # 1. 连接到 Planner 端点
    ws_url = "ws://localhost:8000/mcp/ws/planner"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ 连接到 CodeMCP Planner")
            
            # 2. 创建计划消息
            plan_message = {
                "message_id": f"plan-{uuid.uuid4().hex[:8]}",
                "message_type": "plan_create",
                "source": "openclaw-planner",
                "destination": "server",
                "timestamp": datetime.now().isoformat(),
                "priority": "normal",
                "metadata": {},
                "data": {
                    "system_name": "用户认证系统",
                    "description": "完整的用户注册、登录、权限管理系统",
                    "blocks": [
                        {
                            "name": "用户注册模块",
                            "description": "新用户注册功能",
                            "features": [
                                {
                                    "name": "邮箱注册",
                                    "description": "通过邮箱注册新用户",
                                    "test_command": "pytest tests/auth/test_registration.py::test_email_registration"
                                },
                                {
                                    "name": "手机号注册",
                                    "description": "通过手机号注册新用户",
                                    "test_command": "pytest tests/auth/test_registration.py::test_phone_registration"
                                }
                            ]
                        },
                        {
                            "name": "用户登录模块",
                            "description": "用户登录和会话管理",
                            "features": [
                                {
                                    "name": "密码登录",
                                    "description": "用户名密码登录",
                                    "test_command": "pytest tests/auth/test_login.py::test_password_login"
                                },
                                {
                                    "name": "JWT令牌验证",
                                    "description": "JWT令牌生成和验证",
                                    "test_command": "pytest tests/auth/test_jwt.py::test_jwt_generation"
                                }
                            ]
                        }
                    ]
                }
            }
            
            # 3. 发送计划
            print("📤 发送计划创建请求...")
            await websocket.send(json.dumps(plan_message))
            
            # 4. 接收响应
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"📥 收到响应: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("message_type") == "plan_created":
                print("✅ 计划创建成功！")
                return response_data
            else:
                print("⚠️ 计划创建响应格式异常")
                return response_data
                
    except Exception as e:
        print(f"❌ 创建计划失败: {e}")
        return None

# 运行示例
asyncio.run(create_auth_system_plan())
```

## 与 Coding Skill 集成

### 项目计划设计原则
- **角色定位**: 作为全栈软件设计师和项目leader，负责制定完善的计划
- **文档风格**: 计划文档主要给用户审阅，尽量少用代码，多用文字和图表说明
- **图表工具**: 优先使用mermaid图表、流程图、架构图等可视化表达
- **实现分工**: 具体代码实现由Claude Code完成，我们负责计划制定和结果检查
- **沟通重点**: 关注架构设计、模块划分、接口定义、业务流程，而不是具体代码实现

### 使用计划模板
CodeMCP 提供了标准的计划模板，位于：
```
/home/designer/tools/CodeMCP/doc/plan_template.md
```

使用模板创建结构化计划：
```python
def load_plan_template():
    """加载计划模板"""
    with open("/home/designer/tools/CodeMCP/doc/plan_template.md", "r") as f:
        return f.read()

def create_plan_from_template(project_info):
    """基于模板创建计划"""
    template = load_plan_template()
    
    # 替换模板中的占位符
    plan = template.replace("[填写项目名称，如：\"用户认证系统开发\"]", project_info["name"])
    plan = plan.replace("[简要描述项目目标和范围]", project_info["description"])
    
    # 添加具体的blocks和features
    # ... 根据项目信息填充模板
    
    return plan
```

## 高级功能

### 1. 发送完整任务流
```python
async def send_task_flow(websocket, plan_id, task_sequence):
    """发送完整的任务流程到 CodeMCP
    
    Args:
        websocket: WebSocket 连接
        plan_id: 计划ID
        task_sequence: 任务序列，按执行顺序排列
    """
    flow_message = {
        "message_id": f"flow-{uuid.uuid4().hex[:8]}",
        "message_type": "task_flow",
        "source": "openclaw-planner",
        "destination": "server",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "plan_id": plan_id,
            "tasks": task_sequence,
            "flow_type": "sequential",  # sequential, parallel, dependency
            "dependencies": self._calculate_dependencies(task_sequence)
        }
    }
    
    await websocket.send(json.dumps(flow_message))
    response = await websocket.recv()
    return json.loads(response)

def _calculate_dependencies(self, tasks):
    """计算任务依赖关系"""
    dependencies = {}
    for i, task in enumerate(tasks):
        if i > 0:
            # 默认顺序依赖：每个任务依赖前一个任务
            dependencies[task["task_id"]] = [tasks[i-1]["task_id"]]
        else:
            dependencies[task["task_id"]] = []
    return dependencies
```

### 2. 监听feature完成事件并自动git提交
```python
async def monitor_and_commit(websocket, plan_id, repo_path, git_config):
    """监听feature完成事件，自动git提交
    
    Args:
        websocket: WebSocket 连接
        plan_id: 计划ID
        repo_path: Git仓库路径
        git_config: Git配置 {remote_url, branch, user_name, user_email}
    """
    print(f"🔍 开始监听计划 {plan_id} 的feature完成事件...")
    
    # 订阅事件
    subscribe_message = {
        "message_id": f"subscribe-{uuid.uuid4().hex[:8]}",
        "message_type": "event_subscribe",
        "source": "openclaw-planner",
        "destination": "server",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "plan_id": plan_id,
            "event_types": ["feature_completed", "task_completed"]
        }
    }
    
    await websocket.send(json.dumps(subscribe_message))
    
    try:
        while True:
            # 监听事件
            event_data = await websocket.recv()
            event = json.loads(event_data)
            
            if event.get("message_type") == "feature_completed":
                feature_data = event.get("data", {})
                feature_name = feature_data.get("feature_name")
                task_id = feature_data.get("task_id")
                
                print(f"✅ Feature完成: {feature_name} (任务ID: {task_id})")
                
                # 执行git提交
                commit_success = await self._git_commit_feature(
                    repo_path, 
                    feature_name, 
                    feature_data,
                    git_config
                )
                
                if commit_success:
                    # 发送提交确认
                    confirm_message = {
                        "message_id": f"commit-{uuid.uuid4().hex[:8]}",
                        "message_type": "feature_committed",
                        "source": "openclaw-planner",
                        "destination": "server",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "feature_name": feature_name,
                            "task_id": task_id,
                            "commit_hash": commit_success.get("commit_hash"),
                            "commit_message": commit_success.get("commit_message")
                        }
                    }
                    await websocket.send(json.dumps(confirm_message))
                    
    except websockets.exceptions.ConnectionClosed:
        print("📡 连接已关闭，停止监听")
    except Exception as e:
        print(f"❌ 监听错误: {e}")

async def _git_commit_feature(self, repo_path, feature_name, feature_data, git_config):
    """执行git提交
    
    Returns:
        dict: 提交结果 {success: bool, commit_hash: str, commit_message: str}
    """
    import subprocess
    import os
    
    # 切换到仓库目录
    original_cwd = os.getcwd()
    os.chdir(repo_path)
    
    try:
        # 1. 配置git用户
        subprocess.run(["git", "config", "user.name", git_config["user_name"]], check=True)
        subprocess.run(["git", "config", "user.email", git_config["user_email"]], check=True)
        
        # 2. 检查是否有更改
        status_result = subprocess.run(["git", "status", "--porcelain"], 
                                      capture_output=True, text=True)
        if not status_result.stdout.strip():
            print("   ⚠️ 没有文件更改，跳过提交")
            return {"success": False, "reason": "no_changes"}
        
        # 3. 添加所有更改
        subprocess.run(["git", "add", "."], check=True)
        
        # 4. 创建提交消息
        commit_message = f"feat: {feature_name}\n\n"
        commit_message += f"完成功能: {feature_name}\n"
        commit_message += f"描述: {feature_data.get('description', '')}\n"
        commit_message += f"测试命令: {feature_data.get('test_command', '')}\n"
        commit_message += f"完成时间: {datetime.now().isoformat()}\n"
        commit_message += f"任务ID: {feature_data.get('task_id', '')}"
        
        # 5. 提交
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True, text=True
        )
        
        if commit_result.returncode != 0:
            print(f"   ❌ Git提交失败: {commit_result.stderr}")
            return {"success": False, "reason": "commit_failed"}
        
        # 6. 获取提交哈希
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        commit_hash = hash_result.stdout.strip()
        
        # 7. 推送到远程仓库（如果配置了）
        if git_config.get("remote_url") and git_config.get("branch"):
            print(f"   📤 推送到远程仓库: {git_config['remote_url']}")
            push_result = subprocess.run(
                ["git", "push", git_config["remote_url"], git_config["branch"]],
                capture_output=True, text=True
            )
            
            if push_result.returncode != 0:
                print(f"   ⚠️ 推送失败: {push_result.stderr}")
                # 仍然返回成功，因为本地提交成功了
        
        print(f"   ✅ Git提交成功: {commit_hash[:8]}")
        return {
            "success": True,
            "commit_hash": commit_hash,
            "commit_message": commit_message
        }
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Git操作失败: {e}")
        return {"success": False, "reason": str(e)}
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
```

### 3. 完整的开发工作流
```python
async def complete_development_workflow(project_info, repo_path, git_config):
    """完整的开发工作流：创建计划 → 发送任务 → 监听完成 → 自动提交
    
    Args:
        project_info: 项目信息
        repo_path: Git仓库路径
        git_config: Git配置
    """
    
    # 1. 连接到 Planner
    ws_url = "ws://localhost:8000/mcp/ws/planner"
    async with websockets.connect(ws_url) as websocket:
        
        # 2. 创建计划
        print("📋 创建项目计划...")
        plan_response = await self.create_plan(
            websocket,
            system_name=project_info["name"],
            description=project_info["description"],
            blocks=project_info["blocks"]
        )
        
        if plan_response.get("message_type") != "plan_created":
            print("❌ 计划创建失败")
            return False
        
        plan_id = plan_response["data"]["plan_id"]
        print(f"✅ 计划创建成功: {plan_id}")
        
        # 3. 发送任务流
        print("🚀 发送任务流...")
        task_sequence = self._create_task_sequence(project_info["blocks"])
        flow_response = await self.send_task_flow(websocket, plan_id, task_sequence)
        
        if flow_response.get("message_type") != "flow_accepted":
            print("❌ 任务流发送失败")
            return False
        
        print("✅ 任务流发送成功，等待Executor执行...")
        
        # 4. 监听完成事件并自动提交
        print("🔍 开始监听feature完成事件...")
        await self.monitor_and_commit(websocket, plan_id, repo_path, git_config)
        
        return True

def _create_task_sequence(self, blocks):
    """从blocks创建任务序列"""
    task_sequence = []
    task_id = 1
    
    for block in blocks:
        for feature in block.get("features", []):
            task = {
                "task_id": f"task-{task_id:03d}",
                "block_name": block["name"],
                "feature_name": feature["name"],
                "description": feature["description"],
                "test_command": feature["test_command"],
                "priority": feature.get("priority", 0),
                "estimated_time": 1800,  # 30分钟
                "dependencies": []  # 由系统计算
            }
            task_sequence.append(task)
            task_id += 1
    
    return task_sequence
```

### 4. 计划状态监控
```python
async def check_plan_status(websocket, plan_id):
    """检查计划状态"""
    status_message = {
        "message_id": f"status-{uuid.uuid4().hex[:8]}",
        "message_type": "plan_status",
        "source": "openclaw-planner",
        "destination": "server",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "plan_id": plan_id
        }
    }
    
    await websocket.send(json.dumps(status_message))
    response = await websocket.recv()
    return json.loads(response)
```

### 5. 任务重新规划
```python
async def replan_failed_tasks(websocket, plan_id, failed_tasks):
    """重新规划失败的任务"""
    replan_message = {
        "message_id": f"replan-{uuid.uuid4().hex[:8]}",
        "message_type": "plan_replan",
        "source": "openclaw-planner",
        "destination": "server",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "plan_id": plan_id,
            "failed_tasks": failed_tasks,
            "reason": "任务执行失败，需要更细粒度的分解"
        }
    }
    
    await websocket.send(json.dumps(replan_message))
    response = await websocket.recv()
    return json.loads(response)
```

### 6. 批量创建计划
```python
async def create_multiple_plans(project_list):
    """批量创建多个项目计划"""
    results = []
    
    for project in project_list:
        print(f"📋 创建计划: {project['name']}")
        
        # 连接到服务器
        ws_url = "ws://localhost:8000/mcp/ws/planner"
        async with websockets.connect(ws_url) as websocket:
            
            # 创建计划消息
            plan_message = create_plan_message(
                system_name=project["name"],
                description=project["description"],
                blocks=project.get("blocks", [])
            )
            
            # 发送计划
            await websocket.send(json.dumps(plan_message))
            
            # 接收响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                results.append({
                    "project": project["name"],
                    "success": response_data.get("message_type") == "plan_created",
                    "response": response_data
                })
            except asyncio.TimeoutError:
                results.append({
                    "project": project["name"],
                    "success": False,
                    "error": "响应超时"
                })
    
    return results
```

## 故障排除

### 常见问题

#### 1. 连接被拒绝
**症状**: `websockets.exceptions.InvalidStatus: server rejected WebSocket connection: HTTP 403`

**解决方案**:
```bash
# 检查服务器是否运行
curl http://localhost:8000/

# 检查防火墙设置
# 确保端口8000开放

# 重启服务器
cd /home/designer/tools/CodeMCP && ./start.sh --server --dev
```

#### 2. 计划创建无响应
**症状**: 发送计划消息后没有响应

**解决方案**:
```python
# 增加超时时间
response = await asyncio.wait_for(websocket.recv(), timeout=30.0)

# 检查消息格式
print(f"发送的消息: {json.dumps(plan_message, indent=2)}")

# 发送ping测试连接
ping_message = {
    "message_type": "ping",
    "source": "test",
    "destination": "server"
}
await websocket.send(json.dumps(ping_message))
ping_response = await websocket.recv()
print(f"Ping响应: {ping_response}")
```

#### 3. 消息格式错误
**症状**: 服务器返回错误消息

**解决方案**:
```python
# 确保消息包含所有必需字段
required_fields = [
    "message_id", "message_type", "source", "destination",
    "timestamp", "priority", "metadata", "data"
]

# 使用正确的message_type
# plan_create - 创建新计划
# plan_status - 查询计划状态
# ping - 测试连接
```

## 最佳实践

### 1. 计划设计原则
- **逐步细化**: 从系统级到测试级的逐步分解
- **可测试性**: 每个功能点必须有明确的测试命令
- **独立性**: 尽量减少任务间的依赖
- **优先级**: 明确设置任务优先级（0为最高）

### 2. 消息处理
- **唯一ID**: 为每个消息生成唯一ID
- **时间戳**: 包含ISO格式的时间戳
- **错误处理**: 处理超时和异常情况
- **日志记录**: 记录重要的交互信息

### 3. 与Executor协同
- **任务粒度**: 创建适合Executor执行的任务
- **依赖管理**: 明确任务间的依赖关系
- **结果验证**: 设计验证任务结果的机制
- **失败处理**: 规划任务失败时的处理策略

## 工具集成

### 使用bash工具
```bash
# 测试连接
curl -s http://localhost:8000/mcp/info | python -m json.tool

# 使用websocat测试WebSocket
websocat ws://localhost:8000/mcp/ws/planner

# 发送测试消息
echo '{"message_type": "ping", "source": "test", "destination": "server"}' | websocat ws://localhost:8000/mcp/ws/planner
```

### 与coding-agent协同
```python
# 创建计划后，使用coding-agent执行具体开发任务
plan = await create_plan(...)

if plan["success"]:
    # 启动coding-agent执行开发任务
    coding_agent_command = f"codex exec '根据计划 {plan['id']} 开始开发'"
    # ... 执行coding-agent
```

## 示例项目

### 完整的工作流程示例
```python
import asyncio
import json
import websockets
from datetime import datetime
import uuid

class CodeMCPPlanner:
    """CodeMCP Planner 客户端"""
    
    def __init__(self, planner_id="openclaw-planner"):
        self.planner_id = planner_id
        self.ws_url = "ws://localhost:8000/mcp/ws/planner"
        
    async def create_project_plan(self, project_name, requirements):
        """创建完整的项目计划"""
        
        # 1. 分析需求，分解为四层结构
        system_plan = self.analyze_requirements(project_name, requirements)
        
        # 2. 连接到服务器
        async with websockets.connect(self.ws_url) as websocket:
            
            # 3. 创建计划消息
            plan_message = {
                "message_id": f"plan-{uuid.uuid4().hex[:8]}",
                "message_type": "plan_create",
                "source": self.planner_id,
                "destination": "server",
                "timestamp": datetime.now().isoformat(),
                "priority": "normal",
                "metadata": {},
                "data": system_plan
            }
            
            # 4. 发送计划
            await websocket.send(json.dumps(plan_message))
            
            # 5. 接收响应
            response = await websocket.recv()
            response_data = json.loads(response)
            
            return response_data
    
    def analyze_requirements(self, project_name, requirements):
        """分析需求，创建四层结构"""
        # 这里实现需求分析逻辑
        # 返回符合CodeMCP四层数据模型的结构
        
        return {
            "system_name": project_name,
            "description": requirements,
            "blocks": [
                # ... 根据需求生成的blocks
            ]
        }

# 使用示例
async def main():
    planner = CodeMCPPlanner()
    
    project_requirements = """
    开发一个博客系统，需要以下功能：
    1. 用户注册和登录
    2. 文章发布和管理
    3. 评论系统
    4. 文章分类和标签
    5. 搜索功能
    """
    
    result = await planner.create_project_plan("博客系统开发", project_requirements)
    print(f"计划创建结果: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 总结

CodeMCP Planner Skill 使你能够：
1. ✅ 连接到 CodeMCP AI协同编排服务器
2. ✅ 创建结构化的软件开发计划
3. ✅ 管理四层数据模型(System→Block→Feature→Test)
4. ✅ 协调多个AI agent协同工作
5. ✅ 监控计划执行状态
6. ✅ 处理任务失败和重新规划

通过这个Skill，你可以作为专业的项目规划器，为复杂的软件开发项目创建可执行、可监控、可修复的AI协同开发计划。