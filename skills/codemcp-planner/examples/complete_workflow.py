#!/usr/bin/env python3
"""
完整的开发工作流示例
演示：创建计划 → 发送任务流 → 监听完成 → 自动git提交
"""

import asyncio
import json
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codemcp_client import CodeMCPPlannerClient, PlanBuilder


class CompleteDevelopmentWorkflow:
    """完整的开发工作流"""
    
    def __init__(self):
        self.client = CodeMCPPlannerClient(
            host="localhost",
            port=8000,
            planner_id="openclaw-workflow"
        )
    
    def create_sample_project(self):
        """创建示例项目"""
        print("📋 创建示例项目...")
        
        # 创建系统
        system = PlanBuilder.create_system(
            name="API网关系统",
            description="微服务API网关，支持路由、认证、限流等功能"
        )
        
        # 添加路由模块
        system = PlanBuilder.add_block(
            system,
            name="路由模块",
            description="请求路由和转发",
            priority=0
        )
        
        # 为路由模块添加功能
        routing_block = system["blocks"][0]
        PlanBuilder.add_feature(
            routing_block,
            name="路径路由",
            description="根据URL路径路由请求",
            test_command="pytest tests/routing/test_path_routing.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            routing_block,
            name="负载均衡",
            description="请求的负载均衡",
            test_command="pytest tests/routing/test_load_balancing.py -v",
            priority=1
        )
        
        # 添加认证模块
        system = PlanBuilder.add_block(
            system,
            name="认证模块",
            description="API认证和授权",
            priority=1
        )
        
        # 为认证模块添加功能
        auth_block = system["blocks"][1]
        PlanBuilder.add_feature(
            auth_block,
            name="JWT认证",
            description="JWT令牌验证",
            test_command="pytest tests/auth/test_jwt_auth.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            auth_block,
            name="API密钥认证",
            description="API密钥验证",
            test_command="pytest tests/auth/test_api_key_auth.py -v",
            priority=1
        )
        
        # 添加限流模块
        system = PlanBuilder.add_block(
            system,
            name="限流模块",
            description="请求限流和配额",
            priority=2
        )
        
        # 为限流模块添加功能
        rate_limit_block = system["blocks"][2]
        PlanBuilder.add_feature(
            rate_limit_block,
            name="令牌桶限流",
            description="基于令牌桶算法的限流",
            test_command="pytest tests/rate_limit/test_token_bucket.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            rate_limit_block,
            name="滑动窗口限流",
            description="基于滑动窗口的限流",
            test_command="pytest tests/rate_limit/test_sliding_window.py -v",
            priority=1
        )
        
        return system
    
    def create_task_sequence(self, system):
        """从系统创建任务序列"""
        print("🔄 创建任务序列...")
        
        tasks = []
        task_id = 1
        
        for block in system["blocks"]:
            for feature in block.get("features", []):
                task = {
                    "task_id": f"task-{task_id:03d}",
                    "block_name": block["name"],
                    "feature_name": feature["name"],
                    "description": feature["description"],
                    "test_command": feature["test_command"],
                    "priority": feature.get("priority", 0),
                    "estimated_time": 1800,  # 30分钟
                    "resources": ["python", "fastapi", "pytest"],
                    "dependencies": []  # 由系统计算
                }
                tasks.append(task)
                task_id += 1
        
        print(f"   创建了 {len(tasks)} 个任务")
        return tasks
    
    def get_git_config(self):
        """获取Git配置"""
        # 这里应该是从配置文件中读取
        # 为了示例，我们使用硬编码值
        return {
            "user_name": "OpenClaw AI",
            "user_email": "ai@openclaw.example.com",
            "remote_url": "https://github.com/your-username/api-gateway.git",
            "branch": "main"
        }
    
    async def run_workflow(self, repo_path=None):
        """运行完整的工作流"""
        print("=" * 60)
        print("CodeMCP 完整开发工作流")
        print("=" * 60)
        
        # 如果没有提供repo_path，使用临时目录
        if repo_path is None:
            import tempfile
            repo_path = tempfile.mkdtemp(prefix="codemcp_workflow_")
            print(f"📁 使用临时目录: {repo_path}")
            
            # 初始化git仓库
            import subprocess
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            print("   ✅ 初始化git仓库")
        
        # 获取git配置
        git_config = self.get_git_config()
        
        try:
            # 1. 连接到服务器
            print("\n1. 连接到 CodeMCP 服务器...")
            websocket = await self.client.connect()
            
            # 2. 测试连接
            print("\n2. 测试连接...")
            ping_response = await self.client.ping(websocket)
            if ping_response.get("message_type") == "pong":
                print("   ✅ 连接测试成功")
            else:
                print(f"   ⚠️ 连接测试响应: {ping_response.get('message_type')}")
                return False
            
            # 3. 创建项目计划
            print("\n3. 创建项目计划...")
            system = self.create_sample_project()
            
            plan_response = await self.client.create_plan(
                websocket=websocket,
                system_name=system["system_name"],
                description=system["description"],
                blocks=system["blocks"],
                priority="high"
            )
            
            if plan_response.get("message_type") != "plan_created":
                print(f"   ❌ 计划创建失败: {plan_response}")
                return False
            
            plan_id = plan_response.get("data", {}).get("plan_id")
            print(f"   ✅ 计划创建成功: {plan_id}")
            
            # 4. 发送任务流
            print("\n4. 发送任务流...")
            tasks = self.create_task_sequence(system)
            
            flow_response = await self.client.send_task_flow(
                websocket=websocket,
                plan_id=plan_id,
                tasks=tasks,
                flow_type="sequential"
            )
            
            if flow_response.get("message_type") != "flow_accepted":
                print(f"   ❌ 任务流发送失败: {flow_response}")
                return False
            
            print(f"   ✅ 任务流发送成功，{len(tasks)} 个任务已排队")
            
            # 5. 显示任务信息
            print("\n5. 任务信息:")
            for i, task in enumerate(tasks, 1):
                print(f"   {i:2d}. [{task['task_id']}] {task['feature_name']}")
                print(f"       模块: {task['block_name']}")
                print(f"       优先级: {task['priority']}")
                print(f"       测试: {task['test_command']}")
            
            # 6. 开始监听和自动提交
            print("\n6. 开始监听feature完成事件...")
            print("   🎯 等待Executor执行任务...")
            print("   💾 任务完成后将自动git提交")
            print("   🛑 按 Ctrl+C 停止监听")
            
            # 在实际使用中，这里应该在一个单独的线程或进程中运行
            # 为了示例，我们运行一个简化的版本
            await self.simulate_monitoring(websocket, plan_id, repo_path, git_config)
            
            # 7. 关闭连接
            print("\n7. 关闭连接...")
            await websocket.close()
            print("   ✅ 连接已关闭")
            
            print("\n" + "=" * 60)
            print("🎉 工作流执行完成!")
            print("=" * 60)
            
            return True
            
        except ConnectionError as e:
            print(f"\n❌ 连接错误: {e}")
            return False
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断")
            return True
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def simulate_monitoring(self, websocket, plan_id, repo_path, git_config):
        """模拟监听过程（实际应该监听真实事件）"""
        print("\n🔍 模拟监听过程...")
        
        # 在实际应用中，这里应该持续监听websocket事件
        # 为了示例，我们模拟几个事件
        
        # 模拟第一个feature完成
        await asyncio.sleep(2)
        print("   📢 模拟: feature '路径路由' 完成")
        
        # 模拟git提交
        mock_feature_data = {
            "feature_name": "路径路由",
            "description": "根据URL路径路由请求",
            "test_command": "pytest tests/routing/test_path_routing.py -v",
            "task_id": "task-001"
        }
        
        commit_result = await self.client._git_commit_feature(
            repo_path,
            "路径路由",
            mock_feature_data,
            git_config
        )
        
        if commit_result.get("success"):
            print(f"   ✅ 模拟git提交成功: {commit_result.get('commit_hash', '')[:8]}")
        else:
            print(f"   ⚠️ 模拟git提交失败: {commit_result.get('reason')}")
        
        # 模拟第二个feature完成
        await asyncio.sleep(2)
        print("   📢 模拟: feature 'JWT认证' 完成")
        
        mock_feature_data = {
            "feature_name": "JWT认证",
            "description": "JWT令牌验证",
            "test_command": "pytest tests/auth/test_jwt_auth.py -v",
            "task_id": "task-003"
        }
        
        commit_result = await self.client._git_commit_feature(
            repo_path,
            "JWT认证",
            mock_feature_data,
            git_config
        )
        
        if commit_result.get("success"):
            print(f"   ✅ 模拟git提交成功: {commit_result.get('commit_hash', '')[:8]}")
        else:
            print(f"   ⚠️ 模拟git提交失败: {commit_result.get('reason')}")
        
        print("\n   🎯 在实际应用中，这里会持续监听直到所有任务完成")
        print("   💾 每个feature完成后都会自动git提交")


async def quick_test():
    """快速测试"""
    print("\n快速测试 CodeMCP 连接和基本功能...")
    
    workflow = CompleteDevelopmentWorkflow()
    
    try:
        # 测试连接
        client = workflow.client
        websocket = await client.connect()
        
        # 发送ping
        ping_response = await client.ping(websocket)
        print(f"   Ping响应: {ping_response.get('message_type')}")
        
        # 测试计划构建
        system = workflow.create_sample_project()
        print(f"   创建系统: {system['system_name']}")
        print(f"   模块数量: {len(system['blocks'])}")
        
        # 测试任务序列
        tasks = workflow.create_task_sequence(system)
        print(f"   任务数量: {len(tasks)}")
        
        await websocket.close()
        print("✅ 快速测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False


if __name__ == "__main__":
    print("CodeMCP Planner Skill - 完整开发工作流示例")
    print("=" * 60)
    
    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 快速测试模式
            success = asyncio.run(quick_test())
        elif sys.argv[1] == "repo" and len(sys.argv) > 2:
            # 指定仓库路径
            repo_path = sys.argv[2]
            workflow = CompleteDevelopmentWorkflow()
            success = asyncio.run(workflow.run_workflow(repo_path))
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("\n使用方法:")
            print("  python complete_workflow.py          # 运行完整示例（使用临时目录）")
            print("  python complete_workflow.py test     # 快速测试")
            print("  python complete_workflow.py repo /path/to/repo  # 使用指定仓库")
            success = False
    else:
        # 完整示例模式
        workflow = CompleteDevelopmentWorkflow()
        success = asyncio.run(workflow.run_workflow())
    
    sys.exit(0 if success else 1)