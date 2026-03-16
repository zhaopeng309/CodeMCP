#!/usr/bin/env python3
"""
基础 Executor 示例
演示如何连接到 CodeMCP 服务器并执行任务
"""

import asyncio
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codemcp_executor import CodeMCPExecutor, TaskExecutor


async def basic_executor_demo():
    """基础 Executor 演示"""
    
    print("=" * 60)
    print("CodeMCP Executor 基础演示")
    print("=" * 60)
    
    # 1. 创建执行器
    executor = CodeMCPExecutor(
        executor_id="demo-executor-001",
        capabilities=["python", "pytest", "shell", "node"],
        debug=True
    )
    
    try:
        # 2. 连接到服务器
        print("\n1. 连接到 CodeMCP 服务器...")
        connected = await executor.connect()
        if not connected:
            print("   ❌ 连接失败")
            return False
        
        print("   ✅ 连接成功")
        
        # 3. 测试连接
        print("\n2. 测试连接...")
        ping_response = await executor.ping()
        if ping_response.get("message_type") == "pong":
            print("   ✅ Ping测试成功")
        else:
            print(f"   ⚠️ Ping响应: {ping_response.get('message_type')}")
        
        # 4. 获取任务
        print("\n3. 获取任务...")
        task = await executor.fetch_task()
        
        if task:
            task_id = task.get("task_id", "unknown")
            command = task.get("command", "")
            description = task.get("description", "无描述")
            
            print(f"   📥 获取到任务: {task_id}")
            print(f"      描述: {description}")
            print(f"      命令: {command}")
            
            # 分析命令
            analysis = TaskExecutor.analyze_command(command)
            print(f"      分析: {analysis['type']} ({analysis['complexity']})")
            print(f"      预估时间: {analysis['estimated_time']}秒")
            
            # 5. 执行任务
            print("\n4. 执行任务...")
            result = await executor.execute_task(task)
            
            print(f"   🚀 执行结果:")
            print(f"      成功: {'是' if result['success'] else '否'}")
            print(f"      耗时: {result.get('duration', 0):.1f}秒")
            print(f"      退出码: {result.get('exit_code', 'N/A')}")
            
            if result["output"]:
                output_preview = result["output"][:200]
                if len(result["output"]) > 200:
                    output_preview += "..."
                print(f"      输出预览: {output_preview}")
            
            if result["error"]:
                error_preview = result["error"][:200]
                if len(result["error"]) > 200:
                    error_preview += "..."
                print(f"      错误: {error_preview}")
            
            # 6. 提交结果
            print("\n5. 提交结果...")
            success = await executor.submit_result(
                task_id=task_id,
                success=result["success"],
                output=result["output"],
                error_message=result["error"],
                duration=result.get("duration", 0)
            )
            
            if success:
                print("   ✅ 结果提交成功")
            else:
                print("   ❌ 结果提交失败")
                
        else:
            print("   📭 没有可用任务")
            print("\n   提示: 需要先有Planner创建计划并生成任务")
            print("   可以运行: python examples/create_test_plan.py")
        
        # 7. 关闭连接
        print("\n6. 关闭连接...")
        await executor.close()
        print("   ✅ 连接已关闭")
        
        print("\n" + "=" * 60)
        print("基础演示完成!")
        print("=" * 60)
        
        return True
        
    except ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        print("\n请确保:")
        print("1. CodeMCP 服务器正在运行")
        print("2. 运行: cd /home/designer/tools/CodeMCP && ./start.sh --server --dev")
        print("3. 服务器地址: ws://localhost:8000/mcp/ws/executor")
        return False
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_local_execution():
    """测试本地命令执行（不连接服务器）"""
    print("\n" + "=" * 60)
    print("本地命令执行测试")
    print("=" * 60)
    
    # 创建执行器但不连接
    executor = CodeMCPExecutor()
    
    # 测试命令
    test_commands = [
        {
            "command": "echo 'Hello, CodeMCP!'",
            "type": "shell",
            "description": "简单echo命令测试"
        },
        {
            "command": "python -c \"print('Python test:', 2+3)\"",
            "type": "python_script",
            "description": "Python表达式测试"
        },
        {
            "command": "pytest --version",
            "type": "pytest",
            "description": "pytest版本测试"
        }
    ]
    
    for i, test_cmd in enumerate(test_commands, 1):
        print(f"\n{i}. 测试命令: {test_cmd['description']}")
        print(f"   命令: {test_cmd['command']}")
        
        result = await executor.execute_task(test_cmd)
        
        print(f"   结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"   输出: {result['output'].strip()}")
        
        if result["error"]:
            print(f"   错误: {result['error']}")
    
    print("\n" + "=" * 60)
    print("本地测试完成!")
    print("=" * 60)


async def check_server_status():
    """检查服务器状态"""
    print("\n" + "=" * 60)
    print("服务器状态检查")
    print("=" * 60)
    
    import aiohttp
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("/mcp/info", "MCP服务器信息"),
        ("/mcp/health", "健康检查"),
        ("/docs", "API文档"),
        ("/redoc", "交互式文档")
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, description in endpoints:
            url = base_url + endpoint
            try:
                async with session.get(url, timeout=5) as response:
                    status = "✅ 正常" if response.status == 200 else f"⚠️ {response.status}"
                    print(f"{description:20} {status} ({url})")
            except Exception as e:
                print(f"{description:20} ❌ 失败: {e}")
    
    print("\nWebSocket端点:")
    print(f"  Planner:  ws://localhost:8000/mcp/ws/planner")
    print(f"  Executor: ws://localhost:8000/mcp/ws/executor")
    
    print("\n" + "=" * 60)
    print("状态检查完成!")
    print("=" * 60)


if __name__ == "__main__":
    print("CodeMCP Executor Skill - 基础示例")
    print("=" * 60)
    
    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 本地测试模式
            asyncio.run(test_local_execution())
        elif sys.argv[1] == "status":
            # 状态检查模式
            asyncio.run(check_server_status())
        elif sys.argv[1] == "continuous":
            # 持续执行模式
            from codemcp_executor import continuous_execution_example
            asyncio.run(continuous_execution_example())
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("\n使用方法:")
            print("  python basic_executor.py          # 运行基础演示")
            print("  python basic_executor.py test     # 本地命令测试")
            print("  python basic_executor.py status   # 服务器状态检查")
            print("  python basic_executor.py continuous # 持续执行模式")
            sys.exit(1)
    else:
        # 基础演示模式
        success = asyncio.run(basic_executor_demo())
        sys.exit(0 if success else 1)