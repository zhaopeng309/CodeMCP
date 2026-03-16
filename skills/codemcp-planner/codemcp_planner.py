#!/usr/bin/env python3
"""
CodeMCP Planner 客户端库 - 合并增强版
为 CodeMCP AI协同编排服务器提供Python客户端接口
包含需求分析、任务失败处理、状态监控和用户反馈功能
"""

import asyncio
import json
import uuid
import time
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import websockets

# 导入需求分析器
try:
    from requirements_analyzer import RequirementsAnalyzer
    # 使用类型别名避免类型冲突
    RequirementsAnalyzerClass = RequirementsAnalyzer  # type: ignore
except ImportError:
    # 如果导入失败，创建一个简单的替代类
    class RequirementsAnalyzerClass:
        def analyze_requirements(self, text: str) -> Dict[str, Any]:
            return {"system_name": "默认系统", "description": text[:100], "blocks": []}
        
        def refine_plan_based_on_failure(self, plan: Dict[str, Any],
                                        failed_features: List[str]) -> Dict[str, Any]:
            return plan


class CodeMCPPlannerClient:
    """CodeMCP Planner 客户端 - 合并增强版"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 8000,
                 planner_id: str = "openclaw-planner"):
        """
        初始化 Planner 客户端
        
        Args:
            host: CodeMCP 服务器主机
            port: CodeMCP 服务器端口
            planner_id: Planner 客户端标识
        """
        self.host = host
        self.port = port
        self.planner_id = planner_id
        self.ws_url = f"ws://{host}:{port}/mcp/ws/planner"
        self.requirements_analyzer = RequirementsAnalyzerClass()
        self.user_feedback_callback = None
        
    def set_user_feedback_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        设置用户反馈回调函数
        
        Args:
            callback: 回调函数，接收(消息类型, 数据)参数
        """
        self.user_feedback_callback = callback
    
    def _notify_user(self, message_type: str, data: Dict[str, Any]):
        """通知用户"""
        if self.user_feedback_callback:
            try:
                self.user_feedback_callback(message_type, data)
            except Exception as e:
                print(f"⚠️ 用户反馈回调错误: {e}")
    
    async def connect(self):
        """
        连接到 CodeMCP Planner 端点
        
        Returns:
            WebSocket 连接对象
            
        Raises:
            ConnectionError: 连接失败
        """
        try:
            websocket = await websockets.connect(self.ws_url)
            print(f"✅ 成功连接到 CodeMCP Planner 服务器 ({self.ws_url})")
            self._notify_user("connection_established", {"url": self.ws_url})
            return websocket
        except Exception as e:
            error_msg = f"连接失败: {e}"
            self._notify_user("connection_failed", {"error": error_msg})
            raise ConnectionError(error_msg)
    
    def _create_message(self, 
                       message_type: str, 
                       data: Dict[str, Any],
                       priority: str = "normal") -> Dict[str, Any]:
        """
        创建标准消息格式
        
        Args:
            message_type: 消息类型
            data: 消息数据
            priority: 消息优先级
            
        Returns:
            标准化的消息字典
        """
        return {
            "message_id": f"{message_type}-{uuid.uuid4().hex[:8]}",
            "message_type": message_type,
            "source": self.planner_id,
            "destination": "server",
            "timestamp": datetime.now().isoformat(),
            "priority": priority,
            "metadata": {},
            "data": data
        }
    
    async def ping(self, websocket) -> Dict[str, Any]:
        """
        发送 Ping 消息测试连接
        
        Args:
            websocket: WebSocket 连接
            
        Returns:
            Ping 响应
        """
        ping_message = self._create_message("ping", {})
        await websocket.send(json.dumps(ping_message))
        
        response = await websocket.recv()
        return json.loads(response)
    
    async def analyze_and_create_plan(self,
                                     requirements_text: str,
                                     websocket) -> Dict[str, Any]:
        """
        分析用户需求并创建计划
        
        Args:
            requirements_text: 自然语言需求描述
            websocket: WebSocket 连接
            
        Returns:
            计划创建响应
        """
        print("🔍 分析用户需求...")
        self._notify_user("requirements_analysis_started", {"requirements": requirements_text[:200]})
        
        # 分析需求
        analyzed_plan = self.requirements_analyzer.analyze_requirements(requirements_text)
        
        print(f"📋 生成计划: {analyzed_plan['system_name']}")
        self._notify_user("plan_generated", {
            "system_name": analyzed_plan["system_name"],
            "blocks_count": len(analyzed_plan["blocks"]),
            "total_features": sum(len(block["features"]) for block in analyzed_plan["blocks"])
        })
        
        # 创建计划
        plan_response = await self.create_plan(
            websocket=websocket,
            system_name=analyzed_plan["system_name"],
            description=analyzed_plan["description"],
            blocks=analyzed_plan["blocks"]
        )
        
        return plan_response
    
    async def create_plan(self,
                         websocket,
                         system_name: str,
                         description: str,
                         blocks: List[Dict[str, Any]],
                         priority: str = "normal") -> Dict[str, Any]:
        """
        创建新计划
        
        Args:
            websocket: WebSocket 连接
            system_name: 系统名称
            description: 系统描述
            blocks: 模块列表
            priority: 计划优先级
            
        Returns:
            计划创建响应
        """
        plan_data = {
            "system_name": system_name,
            "description": description,
            "blocks": blocks
        }
        
        plan_message = self._create_message("plan_create", plan_data, priority)
        
        print(f"📤 发送计划创建请求: {system_name}")
        self._notify_user("plan_creation_started", {"system_name": system_name})
        
        await websocket.send(json.dumps(plan_message))
        
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("message_type") == "plan_created":
            print(f"✅ 计划创建成功: {system_name}")
            plan_id = response_data.get("data", {}).get("plan_id")
            self._notify_user("plan_created", {
                "system_name": system_name,
                "plan_id": plan_id,
                "blocks_count": len(blocks)
            })
        else:
            print(f"⚠️ 计划创建响应: {response_data.get('message_type')}")
            self._notify_user("plan_creation_failed", {
                "system_name": system_name,
                "response": response_data
            })
            
        return response_data
    
    async def get_plan_status(self,
                            websocket,
                            plan_id: str) -> Dict[str, Any]:
        """
        获取计划状态
        
        Args:
            websocket: WebSocket 连接
            plan_id: 计划ID
            
        Returns:
            计划状态响应
        """
        status_data = {
            "plan_id": plan_id
        }
        
        status_message = self._create_message("plan_status", status_data)
        await websocket.send(json.dumps(status_message))
        
        response = await websocket.recv()
        return json.loads(response)
    
    async def send_task_flow(self,
                           websocket,
                           plan_id: str,
                           tasks: List[Dict[str, Any]],
                           flow_type: str = "sequential") -> Dict[str, Any]:
        """
        发送任务流到 CodeMCP
        
        Args:
            websocket: WebSocket 连接
            plan_id: 计划ID
            tasks: 任务列表
            flow_type: 流程类型 (sequential, parallel, dependency)
            
        Returns:
            任务流响应
        """
        # 计算依赖关系
        dependencies = self._calculate_dependencies(tasks)
        
        flow_data = {
            "plan_id": plan_id,
            "tasks": tasks,
            "flow_type": flow_type,
            "dependencies": dependencies
        }
        
        flow_message = self._create_message("task_flow", flow_data)
        
        print(f"🚀 发送任务流，包含 {len(tasks)} 个任务")
        self._notify_user("task_flow_sent", {
            "plan_id": plan_id,
            "task_count": len(tasks),
            "flow_type": flow_type
        })
        
        await websocket.send(json.dumps(flow_message))
        
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("message_type") == "flow_accepted":
            print("✅ 任务流发送成功")
            self._notify_user("task_flow_accepted", {
                "plan_id": plan_id,
                "task_count": len(tasks),
                "flow_type": flow_type
            })
        else:
            print(f"⚠️ 任务流响应: {response_data.get('message_type')}")
            self._notify_user("task_flow_rejected", {
                "plan_id": plan_id,
                "response": response_data
            })
            
        return response_data
    
    def _calculate_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        计算任务依赖关系
        
        Args:
            tasks: 任务列表
            
        Returns:
            依赖关系字典 {task_id: [dependent_task_ids]}
        """
        dependencies = {}
        
        for task in tasks:
            task_id = task.get("task_id", f"task-{uuid.uuid4().hex[:8]}")
            dependencies[task_id] = task.get("dependencies", [])
            
        return dependencies
    
    async def subscribe_events(self,
                             websocket,
                             event_types: List[str]) -> Dict[str, Any]:
        """
        订阅事件
        
        Args:
            websocket: WebSocket 连接
            event_types: 事件类型列表
            
        Returns:
            订阅响应
        """
        subscribe_data = {
            "event_types": event_types
        }
        
        subscribe_message = self._create_message("subscribe", subscribe_data)
        await websocket.send(json.dumps(subscribe_message))
        
        response = await websocket.recv()
        return json.loads(response)
    
    async def monitor_and_commit(self,
                               websocket,
                               plan_id: str,
                               repo_path: str,
                               git_config: Dict[str, str],
                               timeout: int = 3600) -> Dict[str, Any]:
        """
        监控任务完成并自动执行 Git 提交
        
        Args:
            websocket: WebSocket 连接
            plan_id: 计划ID
            repo_path: Git 仓库路径
            git_config: Git 配置
            timeout: 超时时间（秒）
            
        Returns:
            监控结果
        """
        print(f"👀 开始监控计划 {plan_id} 的任务完成情况...")
        self._notify_user("monitoring_started", {"plan_id": plan_id})
        
        start_time = time.time()
        completed_features = []
        failed_features = []
        
        try:
            # 订阅相关事件
            await self.subscribe_events(websocket, ["feature_completed", "feature_failed"])
            
            while time.time() - start_time < timeout:
                try:
                    # 设置接收超时
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    event_data = json.loads(response)
                    
                    event_type = event_data.get("message_type")
                    
                    if event_type == "feature_completed":
                        feature_data = event_data.get("data", {})
                        feature_id = feature_data.get("feature_id")
                        feature_name = feature_data.get("feature_name")
                        
                        print(f"✅ 功能点完成: {feature_name} ({feature_id})")
                        self._notify_user("feature_completed", feature_data)
                        
                        completed_features.append(feature_data)
                        
                        # 执行 Git 提交
                        await self._git_commit_feature(repo_path, git_config, feature_data)
                        
                    elif event_type == "feature_failed":
                        feature_data = event_data.get("data", {})
                        feature_id = feature_data.get("feature_id")
                        feature_name = feature_data.get("feature_name")
                        error_msg = feature_data.get("error", "未知错误")
                        
                        print(f"❌ 功能点失败: {feature_name} ({feature_id}) - {error_msg}")
                        self._notify_user("feature_failed", feature_data)
                        
                        failed_features.append(feature_data)
                        
                        # 通知用户任务失败
                        self._notify_user("task_failure_notification", {
                            "plan_id": plan_id,
                            "feature_name": feature_name,
                            "feature_id": feature_id,
                            "error": error_msg
                        })
                        
                except asyncio.TimeoutError:
                    # 超时继续循环
                    continue
                except Exception as e:
                    print(f"⚠️ 事件处理错误: {e}")
                    continue
            
            # 超时处理
            print(f"⏰ 监控超时 ({timeout}秒)")
            self._notify_user("monitoring_timeout", {
                "plan_id": plan_id,
                "completed_count": len(completed_features),
                "failed_count": len(failed_features)
            })
            
        except Exception as e:
            print(f"❌ 监控过程中发生错误: {e}")
            self._notify_user("monitoring_error", {
                "plan_id": plan_id,
                "error": str(e)
            })
            raise
        
        return {
            "plan_id": plan_id,
            "completed_features": completed_features,
            "failed_features": failed_features,
            "monitoring_duration": time.time() - start_time
        }
    
    async def _git_commit_feature(self,
                                repo_path: str,
                                git_config: Dict[str, str],
                                feature_data: Dict[str, Any]):
        """
        执行 Git 提交
        
        Args:
            repo_path: Git 仓库路径
            git_config: Git 配置
            feature_data: 功能点数据
        """
        original_cwd = os.getcwd()
        try:
            # 切换到仓库目录
            os.chdir(repo_path)
            
            # 检查是否有未提交的更改
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            
            if status_result.stdout.strip():
                # 添加所有更改
                subprocess.run(["git", "add", "."], check=True)
                
                # 创建提交消息
                feature_name = feature_data.get("feature_name", "未知功能")
                feature_id = feature_data.get("feature_id", "未知ID")
                commit_message = f"feat: 实现 {feature_name} ({feature_id})"
                
                # 提交更改
                subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    check=True
                )
                
                # 推送到远程仓库
                if git_config.get("push_to_remote", True):
                    remote_name = git_config.get("remote_name", "origin")
                    branch_name = git_config.get("branch_name", "main")
                    
                    subprocess.run(
                        ["git", "push", remote_name, branch_name],
                        check=True
                    )
                    
                    print(f"📤 Git 提交并推送到 {remote_name}/{branch_name}")
                    self._notify_user("git_commit_pushed", {
                        "feature_name": feature_name,
                        "feature_id": feature_id,
                        "remote": remote_name,
                        "branch": branch_name
                    })
                else:
                    print(f"💾 Git 提交完成: {commit_message}")
                    self._notify_user("git_commit_local", {
                        "feature_name": feature_name,
                        "feature_id": feature_id,
                        "commit_message": commit_message
                    })
            else:
                print("📝 没有需要提交的更改")
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git 操作失败: {e}")
            self._notify_user("git_error", {
                "error": str(e),
                "feature_data": feature_data
            })
        except Exception as e:
            print(f"⚠️ Git 提交过程中发生错误: {e}")
            self._notify_user("git_error", {
                "error": str(e),
                "feature_data": feature_data
            })
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
    
    async def replan_tasks(self,
                         websocket,
                         original_plan: Dict[str, Any],
                         failed_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        重新规划失败的任务
        
        Args:
            websocket: WebSocket 连接
            original_plan: 原始计划
            failed_features: 失败的功能点列表
            
        Returns:
            重新规划后的计划
        """
        print("🔄 重新规划失败的任务...")
        self._notify_user("replanning_started", {
            "failed_count": len(failed_features),
            "original_system": original_plan.get("system_name")
        })
        
        # 使用需求分析器重新规划
        # 提取失败功能的名称列表
        failed_feature_names = [feature.get("name", "") for feature in failed_features]
        refined_plan = self.requirements_analyzer.refine_plan_based_on_failure(
            original_plan, failed_feature_names
        )
        
        print(f"📋 重新规划完成: {refined_plan['system_name']}")
        self._notify_user("replanning_completed", {
            "system_name": refined_plan["system_name"],
            "blocks_count": len(refined_plan["blocks"]),
            "total_features": sum(len(block["features"]) for block in refined_plan["blocks"])
        })
        
        # 创建新的计划
        new_plan_response = await self.create_plan(
            websocket=websocket,
            system_name=refined_plan["system_name"],
            description=refined_plan["description"],
            blocks=refined_plan["blocks"]
        )
        
        return {
            "replanned": True,
            "original_plan": original_plan,
            "refined_plan": refined_plan,
            "new_plan_response": new_plan_response,
            "failed_features": failed_features
        }