---
name: codemcp-executor
description: "CodeMCP Executor Skill - 为CodeMCP AI协同编排服务器提供任务执行能力，使AI Agent能够作为执行者角色实现功能feature并完成测试。使用场景：需要作为AI执行者连接到CodeMCP服务器、获取功能实现任务、执行代码实现、运行测试验证、提交执行结果。触发条件：用户提到'执行任务'、'任务执行者'、'CodeMCP执行器'、'功能实现'、'代码实现'、'测试执行'、'自动化测试'等。"
metadata:
  {
    "openclaw": { 
      "emoji": "⚡", 
      "requires": { 
        "anyBins": ["python", "curl", "websocat"],
        "anyFiles": ["/home/designer/tools/CodeMCP/doc/user_guide.md"]
      },
      "recommends": {
        "skills": ["coding-agent", "codemcp-planner"]
      }
    }
  }
---

# CodeMCP Executor Skill

## 🚀 快速开始

### 核心功能
1. **连接到CodeMCP服务器** - 作为AI执行者客户端连接
2. **获取功能实现任务** - 从服务器获取功能feature实现任务
3. **执行代码实现** - 执行代码编写、功能实现、测试验证等命令
4. **提交执行结果** - 将功能实现和测试结果提交回服务器
5. **错误处理和重试** - 支持任务失败重试和问题修复

### 一分钟示例
```python
from codemcp_executor import CodeMCPExecutor

# 创建执行器
executor = CodeMCPExecutor(executor_id="claude-code-executor")

# 连接到CodeMCP
websocket = await executor.connect()

# 获取任务
task = await executor.fetch_task()

# 执行任务
if task:
    result = await executor.execute_task(task)
    
    # 提交结果
    await executor.submit_result(
        task_id=task["task_id"],
        success=result["success"],
        output=result["output"],
        error_message=result["error"]
    )
```

## 概述

CodeMCP Executor Skill 使 AI Agent 能够作为执行者角色连接到 CodeMCP AI协同编排服务器，获取功能feature实现任务，执行代码实现和测试验证，并将结果提交回服务器。这是 CodeMCP 协同工作流的关键组成部分，与 Planner Skill 配合使用，实现"规划-执行-验证"的完整开发流程。

### AI Agent 执行者角色
- **功能实现者**：根据规划的任务实现具体的功能feature
- **代码执行者**：执行代码编写、重构、测试等开发任务
- **测试验证者**：运行测试验证功能实现是否正确
- **结果反馈者**：将执行结果和状态反馈给规划系统

## 架构

```
CodeMCP 服务器 (localhost:8000)
        ↑
        | WebSocket 连接 (任务分配/结果反馈)
        ↓
CodeMCP Executor (AI Agent 执行者)
        ↑
        | 执行功能实现和测试
        ↓
开发环境 (代码编写、测试执行、功能验证)
```

### 工作流程
1. **任务获取**：AI Agent 从服务器获取功能feature实现任务
2. **代码实现**：执行代码编写、功能实现等开发任务
3. **测试验证**：运行测试验证功能实现是否正确
4. **结果提交**：将实现结果和测试状态提交回服务器
5. **状态同步**：服务器更新任务状态，规划系统根据结果调整后续计划

## 安装要求

### 系统要求
- Python 3.8+
- Git
- 网络访问权限

### Python依赖
```bash
pip install websockets aiohttp sqlalchemy
```

### CodeMCP服务器
确保 CodeMCP 服务器正在运行：
```bash
cd /home/designer/tools/CodeMCP
./start.sh --server --dev
```

## 基本使用

### 1. 连接到服务器

```python
import asyncio
from codemcp_executor import CodeMCPExecutor

async def main():
    # 创建执行器实例
    executor = CodeMCPExecutor(
        executor_id="my-executor-001",
        host="localhost",
        port=8000,
        capabilities=["python", "pytest", "shell", "node"]
    )
    
    # 连接到服务器
    connected = await executor.connect()
    if not connected:
        print("连接失败")
        return
    
    print("✅ 成功连接到 CodeMCP 服务器")
    
    # 关闭连接
    await executor.close()

asyncio.run(main())
```

### 2. 获取和执行任务

```python
async def execute_single_task():
    """获取并执行单个任务"""
    executor = CodeMCPExecutor()
    
    if not await executor.connect():
        return
    
    try:
        # 获取任务
        task = await executor.fetch_task()
        
        if not task:
            print("📭 没有可用任务")
            return
        
        print(f"📥 获取到任务: {task['task_id']}")
        print(f"   命令: {task.get('command', 'N/A')}")
        print(f"   描述: {task.get('description', 'N/A')}")
        
        # 执行任务
        result = await executor.execute_task(task)
        
        # 提交结果
        success = await executor.submit_result(
            task_id=task["task_id"],
            success=result["success"],
            output=result["output"],
            error_message=result["error"],
            duration=result["duration"]
        )
        
        if success:
            print(f"✅ 任务 {task['task_id']} 结果提交成功")
        else:
            print(f"❌ 任务结果提交失败")
            
    finally:
        await executor.close()
```

### 3. 持续执行模式

```python
async def continuous_execution():
    """持续获取和执行任务"""
    executor = CodeMCPExecutor()
    
    if not await executor.connect():
        return
    
    print("🚀 进入持续执行模式...")
    print("🛑 按 Ctrl+C 停止")
    
    try:
        while True:
            # 获取任务
            task = await executor.fetch_task()
            
            if task:
                print(f"📥 获取到任务: {task['task_id']}")
                
                # 执行任务
                result = await executor.execute_task(task)
                
                # 提交结果
                await executor.submit_result(
                    task_id=task["task_id"],
                    success=result["success"],
                    output=result["output"],
                    error_message=result["error"]
                )
                
                # 短暂等待
                await asyncio.sleep(1)
            else:
                # 没有任务，等待一段时间再重试
                print("⏳ 等待新任务...")
                await asyncio.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    finally:
        await executor.close()
        print("🔌 连接已关闭")
```

## 高级功能

### 1. 自定义任务执行器

```python
class CustomExecutor(CodeMCPExecutor):
    """自定义执行器，扩展执行能力"""
    
    async def execute_task(self, task: dict) -> dict:
        """自定义任务执行逻辑"""
        
        command = task.get("command", "")
        task_type = task.get("type", "shell")
        
        if task_type == "pytest":
            # 特殊处理pytest命令
            return await self._execute_pytest(command)
        elif task_type == "shell":
            # 执行shell命令
            return await self._execute_shell(command)
        elif task_type == "python_script":
            # 执行Python脚本
            return await self._execute_python_script(command)
        else:
            # 默认执行
            return await super().execute_task(task)
    
    async def _execute_pytest(self, command: str) -> dict:
        """执行pytest命令"""
        import subprocess
        import time
        
        start_time = time.time()
        
        try:
            # 添加详细输出和覆盖率报告
            enhanced_command = f"{command} -v --tb=short --cov=."
            
            result = subprocess.run(
                enhanced_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "duration": duration,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "success": False,
                "output": "",
                "error": f"任务执行超时 ({duration:.1f}秒)",
                "duration": duration,
                "exit_code": -1
            }
    
    async def _execute_python_script(self, script_content: str) -> dict:
        """执行Python脚本"""
        import tempfile
        import subprocess
        import time
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            temp_file = f.name
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "duration": duration,
                "exit_code": result.returncode
            }
            
        finally:
            import os
            os.unlink(temp_file)
```

### 2. 任务结果处理器

```python
class ResultProcessor:
    """任务结果处理器"""
    
    @staticmethod
    def analyze_pytest_output(output: str) -> dict:
        """分析pytest输出"""
        import re
        
        # 提取测试结果
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        skipped_match = re.search(r'(\d+) skipped', output)
        
        # 提取覆盖率
        coverage_match = re.search(r'coverage:.*?(\d+%)', output)
        
        return {
            "passed": int(passed_match.group(1)) if passed_match else 0,
            "failed": int(failed_match.group(1)) if failed_match else 0,
            "skipped": int(skipped_match.group(1)) if skipped_match else 0,
            "coverage": coverage_match.group(1) if coverage_match else "N/A",
            "total": (int(passed_match.group(1)) if passed_match else 0) +
                    (int(failed_match.group(1)) if failed_match else 0) +
                    (int(skipped_match.group(1)) if skipped_match else 0)
        }
    
    @staticmethod
    def format_result_for_display(result: dict) -> str:
        """格式化结果用于显示"""
        if result["success"]:
            return f"✅ 成功 (耗时: {result['duration']:.1f}秒)"
        else:
            return f"❌ 失败 (耗时: {result['duration']:.1f}秒)\n错误: {result['error'][:200]}"
```

### 3. 批量任务执行

```python
async def execute_batch_tasks(max_tasks: int = 10):
    """批量执行任务"""
    executor = CodeMCPExecutor()
    
    if not await executor.connect():
        return
    
    completed_tasks = 0
    failed_tasks = 0
    
    try:
        while completed_tasks < max_tasks:
            # 获取任务
            task = await executor.fetch_task()
            
            if not task:
                print("⏳ 等待新任务...")
                await asyncio.sleep(5)
                continue
            
            print(f"📥 任务 {completed_tasks + 1}/{max_tasks}: {task['task_id']}")
            
            # 执行任务
            result = await executor.execute_task(task)
            
            # 提交结果
            success = await executor.submit_result(
                task_id=task["task_id"],
                success=result["success"],
                output=result["output"],
                error_message=result["error"]
            )
            
            if success and result["success"]:
                completed_tasks += 1
                print(f"✅ 任务完成 ({completed_tasks}/{max_tasks})")
            else:
                failed_tasks += 1
                print(f"❌ 任务失败 ({failed_tasks}次失败)")
            
            # 短暂休息
            await asyncio.sleep(1)
            
    finally:
        await executor.close()
        
    print(f"\n🎉 批量执行完成")
    print(f"   成功: {completed_tasks}")
    print(f"   失败: {failed_tasks}")
```

### 4. 与Planner Skill集成

```python
async def integrated_workflow():
    """与Planner Skill集成的完整工作流"""
    
    # 1. 使用Planner创建计划
    from codemcp_client import CodeMCPPlannerClient, PlanBuilder
    
    planner = CodeMCPPlannerClient()
    planner_ws = await planner.connect()
    
    # 创建测试计划
    test_plan = PlanBuilder.create_system(
        name="测试项目",
        description="自动化测试套件"
    )
    
    # 添加测试模块
    test_plan = PlanBuilder.add_block(
        test_plan,
        name="单元测试模块",
        description="单元测试执行",
        priority=0
    )
    
    # 添加测试功能
    block = test_plan["blocks"][0]
    PlanBuilder.add_feature(
        block,
        name="用户认证测试",
        description="用户认证相关测试",
        test_command="pytest tests/auth/ -v",
        priority=0
    )
    
    # 发送计划
    plan_response = await planner.create_plan(
        planner_ws,
        system_name=test_plan["system_name"],
        description=test_plan["description"],
        blocks=test_plan["blocks"]
    )
    
    plan_id = plan_response["data"]["plan_id"]
    print(f"📋 计划创建成功: {plan_id}")
    
    await planner_ws.close()
    
    # 2. 使用Executor执行任务
    executor = CodeMCPExecutor()
    executor_ws = await executor.connect()
    
    print("🚀 开始执行测试任务...")
    
    # 持续执行任务
    completed = 0
    while completed < 5:  # 最多执行5个任务
        task = await executor.fetch_task()
        
        if task:
            print(f"📥 执行任务: {task.get('description', 'N/A')}")
            
            result = await executor.execute_task(task)
            
            await executor.submit_result(
                task_id=task["task_id"],
                success=result["success"],
                output=result["output"],
                error_message=result["error"]
            )
            
            completed += 1
        else:
            await asyncio.sleep(2)
    
    await executor_ws.close()
    
    print("🎉 集成工作流完成")
```

## 故障排除

### 常见问题

#### 1. 连接失败
```python
# 错误: Connection refused
# 解决方案: 确保CodeMCP服务器正在运行
# cd /home/designer/tools/CodeMCP && ./start.sh --server --dev
```

#### 2. 没有任务可执行
```python
# 错误: 获取任务返回空
# 解决方案: 
# 1. 检查是否有Planner创建了计划
# 2. 检查任务队列状态: curl http://localhost:8000/mcp/queue
```

#### 3. 任务执行超时
```python
# 错误: 任务执行时间过长
# 解决方案: 增加超时时间或优化测试命令
executor = CodeMCPExecutor(task_timeout=600)  # 10分钟超时
```

#### 4. 结果提交失败
```python
# 错误: 无法提交任务结果
# 解决方案: 检查网络连接和服务器状态
# 可以重试提交:
for attempt in range(3):
    success = await executor.submit_result(...)
    if success:
        break
    await asyncio.sleep(2)
```

### 调试模式

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

executor = CodeMCPExecutor(debug=True)
```

## 与Claude Code集成

### 安装到Claude Code

1. **复制Skill文件**
```bash
# 将Skill复制到Claude Code的工作空间
cp -r /home/designer/tools/openclaw/skills/codemcp-executor /path/to/claude-code/skills/
```

2. **配置Claude Code环境**
```python
# 在Claude Code的配置文件中添加:
CODING_SKILLS = [
    "codemcp-executor",
    # ... 其他skills
]

# 配置CodeMCP服务器地址
CODEMCP_SERVER = "ws://localhost:8000"
```

3. **在Claude Code中使用**
```python
# Claude Code可以直接导入和使用
from skills.codemcp_executor.codemcp_executor import CodeMCPExecutor

async def claude_code_task():
    """Claude Code作为Executor执行任务"""
    executor = CodeMCPExecutor(executor_id="claude-code-001")
    
    await executor.connect()
    
    # 获取并执行任务
    task = await executor.fetch_task()
    if task:
        # Claude Code可以在这里添加智能分析
        print(f"Claude Code分析任务: {task}")
        
        # 执行任务
        result = await executor.execute_task(task)
        
        # 提交结果
        await executor.submit_result(
            task_id=task["task_id"],
            success=result["success"],
            output=result["output"],
            error_message=result["error"]
        )
    
    await executor.close()
```

### Claude Code作为智能Executor

Claude Code可以增强Executor的能力：

```python
class ClaudeCodeExecutor(CodeMCPExecutor):
    """Claude Code增强的执行器"""
    
    async def execute_task(self, task: dict) -> dict:
        """智能任务执行"""
        
        # 1. 分析任务
        analysis = self.analyze_task(task)
        print(f"📊 任务分析: {analysis}")
        
        # 2. 智能优化命令
        optimized_command = self.optimize_command(task.get("command", ""))
        
        # 3. 执行命令
        result = await super().execute_task({
            **task,
            "command": optimized_command
        })
        
        # 4. 智能分析结果
        if not result["success"]:
            # 尝试自动修复
            fix_suggestion = self.suggest_fix(result["error"])
            result["analysis"] = fix_suggestion
        
        return result