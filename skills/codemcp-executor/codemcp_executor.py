#!/usr/bin/env python3
"""
CodeMCP Executor 客户端库
为 CodeMCP AI协同编排服务器提供任务执行能力
"""

import asyncio
import json
import uuid
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import websockets
import logging


class CodeMCPExecutor:
    """CodeMCP Executor 客户端"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 8000,
                 executor_id: str = None,
                 capabilities: List[str] = None,
                 task_timeout: int = 300,
                 debug: bool = False):
        """
        初始化 Executor 客户端
        
        Args:
            host: CodeMCP 服务器主机
            port: CodeMCP 服务器端口
            executor_id: Executor 客户端标识
            capabilities: 执行能力列表
            task_timeout: 任务执行超时时间（秒）
            debug: 是否启用调试模式
        """
        self.host = host
        self.port = port
        self.executor_id = executor_id or f"executor-{uuid.uuid4().hex[:8]}"
        self.capabilities = capabilities or ["python", "pytest", "shell", "node", "docker"]
        self.task_timeout = task_timeout
        self.debug = debug
        self.ws_url = f"ws://{host}:{port}/mcp/ws/executor"
        self.websocket = None
        
        # 配置日志
        self.logger = logging.getLogger(f"CodeMCPExecutor-{self.executor_id}")
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    async def connect(self) -> bool:
        """
        连接到 CodeMCP Executor 端点
        
        Returns:
            连接是否成功
            
        Raises:
            ConnectionError: 连接失败
        """
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.logger.info(f"✅ 成功连接到 CodeMCP Executor 服务器 ({self.ws_url})")
            return True
        except Exception as e:
            self.logger.error(f"❌ 连接失败: {e}")
            raise ConnectionError(f"连接失败: {e}")
    
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
            "source": self.executor_id,
            "destination": "server",
            "timestamp": datetime.now().isoformat(),
            "priority": priority,
            "metadata": {},
            "data": data
        }
    
    async def ping(self) -> Dict[str, Any]:
        """
        发送 Ping 消息测试连接
        
        Returns:
            Ping 响应
        """
        if not self.websocket:
            await self.connect()
        
        ping_message = self._create_message("ping", {})
        await self.websocket.send(json.dumps(ping_message))
        
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def fetch_task(self, max_tasks: int = 1) -> Optional[Dict[str, Any]]:
        """
        获取待执行的任务
        
        Args:
            max_tasks: 最大获取任务数
            
        Returns:
            任务数据，如果没有任务则返回None
        """
        if not self.websocket:
            await self.connect()
        
        # 发送任务获取请求
        fetch_data = {
            "executor_id": self.executor_id,
            "capabilities": self.capabilities,
            "max_tasks": max_tasks
        }
        
        fetch_message = self._create_message("task_fetch", fetch_data)
        
        self.logger.info("📤 发送任务获取请求")
        await self.websocket.send(json.dumps(fetch_message))
        
        # 等待响应
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        message_type = response_data.get("message_type")
        
        if message_type == "error":
            error_msg = response_data.get("data", {}).get("error_message", "未知错误")
            self.logger.warning(f"⚠️ 获取任务失败: {error_msg}")
            return None
        elif message_type == "no_tasks":
            self.logger.info("📭 暂无可用任务")
            return None
        elif message_type == "task_assigned":
            task_data = response_data.get("data", {})
            task_id = task_data.get("task_id")
            self.logger.info(f"📥 获取到任务: {task_id}")
            return task_data
        else:
            self.logger.warning(f"⚠️ 未知响应类型: {message_type}")
            return None
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务数据
            
        Returns:
            执行结果
        """
        task_id = task.get("task_id", "unknown")
        command = task.get("command", "")
        task_type = task.get("type", "shell")
        
        self.logger.info(f"🚀 开始执行任务 {task_id}")
        self.logger.info(f"   命令: {command}")
        self.logger.info(f"   类型: {task_type}")
        
        start_time = time.time()
        
        try:
            if task_type == "pytest":
                result = await self._execute_pytest(command)
            elif task_type == "python_script":
                result = await self._execute_python_script(command)
            elif task_type == "shell":
                result = await self._execute_shell(command)
            else:
                result = await self._execute_shell(command)
            
            duration = time.time() - start_time
            result["duration"] = duration
            
            if result["success"]:
                self.logger.info(f"✅ 任务 {task_id} 执行成功 (耗时: {duration:.1f}秒)")
            else:
                self.logger.warning(f"❌ 任务 {task_id} 执行失败 (耗时: {duration:.1f}秒)")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"💥 任务 {task_id} 执行异常: {e}")
            
            return {
                "success": False,
                "output": "",
                "error": f"执行异常: {str(e)}",
                "duration": duration,
                "exit_code": -1
            }
    
    async def _execute_shell(self, command: str) -> Dict[str, Any]:
        """执行shell命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.task_timeout
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"任务执行超时 ({self.task_timeout}秒)",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"执行失败: {str(e)}",
                "exit_code": -1
            }
    
    async def _execute_pytest(self, command: str) -> Dict[str, Any]:
        """执行pytest命令"""
        # 增强pytest命令，添加详细输出
        enhanced_command = f"{command} -v --tb=short"
        
        return await self._execute_shell(enhanced_command)
    
    async def _execute_python_script(self, script_content: str) -> Dict[str, Any]:
        """执行Python脚本"""
        import tempfile
        import os
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            temp_file = f.name
        
        try:
            result = await self._execute_shell(f"python {temp_file}")
            return result
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def submit_result(self,
                          task_id: str,
                          success: bool,
                          output: str = "",
                          error_message: str = "",
                          duration: float = 0.0) -> bool:
        """
        提交任务执行结果
        
        Args:
            task_id: 任务ID
            success: 是否成功
            output: 标准输出
            error_message: 错误信息
            duration: 执行时长（秒）
            
        Returns:
            提交是否成功
        """
        if not self.websocket:
            await self.connect()
        
        result_data = {
            "task_id": task_id,
            "success": success,
            "exit_code": 0 if success else 1,
            "stdout": output,
            "stderr": error_message,
            "duration": duration,
            "error_message": error_message if not success else None
        }
        
        result_message = self._create_message("task_result", result_data)
        
        self.logger.info(f"📤 提交任务结果: {task_id}")
        await self.websocket.send(json.dumps(result_message))
        
        # 等待确认
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        message_type = response_data.get("message_type")
        
        if message_type == "result_accepted":
            self.logger.info(f"✅ 任务结果提交成功: {task_id}")
            return True
        elif message_type == "error":
            error_msg = response_data.get("data", {}).get("error_message", "未知错误")
            self.logger.error(f"❌ 任务结果提交失败: {error_msg}")
            return False
        else:
            self.logger.warning(f"⚠️ 未知响应类型: {message_type}")
            return False
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.logger.info("🔌 连接已关闭")


class TaskExecutor:
    """任务执行器 - 提供高级执行功能"""
    
    @staticmethod
    def analyze_command(command: str) -> Dict[str, Any]:
        """分析命令类型和复杂度"""
        analysis = {
            "type": "unknown",
            "complexity": "low",
            "estimated_time": 30,  # 默认30秒
            "requires": []
        }
        
        if "pytest" in command:
            analysis["type"] = "pytest"
            analysis["complexity"] = "medium"
            analysis["estimated_time"] = 120
            analysis["requires"] = ["python", "pytest"]
            
            # 分析测试范围
            if "::" in command:
                analysis["complexity"] = "low"  # 单个测试函数
            elif "/" in command:
                analysis["complexity"] = "medium"  # 测试文件
            else:
                analysis["complexity"] = "high"  # 整个测试套件
                
        elif "python" in command and ".py" in command:
            analysis["type"] = "python_script"
            analysis["complexity"] = "medium"
            analysis["estimated_time"] = 60
            analysis["requires"] = ["python"]
            
        elif "npm test" in command or "yarn test" in command:
            analysis["type"] = "node_test"
            analysis["complexity"] = "medium"
            analysis["estimated_time"] = 90
            analysis["requires"] = ["node", "npm"]
            
        elif "docker" in command:
            analysis["type"] = "docker"
            analysis["complexity"] = "high"
            analysis["estimated_time"] = 180
            analysis["requires"] = ["docker"]
            
        else:
            analysis["type"] = "shell"
            analysis["complexity"] = "low"
            analysis["estimated_time"] = 30
            analysis["requires"] = ["shell"]
        
        return analysis
    
    @staticmethod
    def optimize_command(command: str, analysis: Dict[str, Any] = None) -> str:
        """优化命令执行"""
        if not analysis:
            analysis = TaskExecutor.analyze_command(command)
        
        optimized = command
        
        if analysis["type"] == "pytest":
            # 添加详细输出和失败时停止
            if "-v" not in command:
                optimized = f"{command} -v"
            if "-x" not in command:
                optimized = f"{optimized} -x"  # 失败时停止
            
        elif analysis["type"] == "shell" and analysis["complexity"] == "high":
            # 为复杂shell命令添加超时
            if "timeout" not in command:
                timeout = min(analysis["estimated_time"] * 2, 600)
                optimized = f"timeout {timeout} {command}"
        
        return optimized
    
    @staticmethod
    def format_output(output: str, max_lines: int = 50) -> str:
        """格式化输出，限制行数"""
        lines = output.split('\n')
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f"\n... (省略 {len(lines) - max_lines} 行)"
        return output


async def example_usage():
    """使用示例"""
    
    print("=" * 60)
    print("CodeMCP Executor 示例")
    print("=" * 60)
    
    # 1. 创建执行器
    executor = CodeMCPExecutor(
        executor_id="example-executor-001",
        capabilities=["python", "pytest", "shell"],
        debug=True
    )
    
    try:
        # 2. 连接到服务器
        print("\n1. 连接到 CodeMCP 服务器...")
        await executor.connect()
        
        # 3. 测试连接
        print("\n2. 测试连接...")
        ping_response = await executor.ping()
        if ping_response.get("message_type") == "pong":
            print("   ✅ 连接测试成功")
        else:
            print(f"   ⚠️ 连接测试响应: {ping_response.get('message_type')}")
        
        # 4. 获取任务
        print("\n3. 获取任务...")
        task = await executor.fetch_task()
        
        if task:
            print(f"   获取到任务: {task.get('task_id')}")
            print(f"   命令: {task.get('command', 'N/A')}")
            print(f"   描述: {task.get('description', 'N/A')}")
            
            # 5. 执行任务
            print("\n4. 执行任务...")
            result = await executor.execute_task(task)
            
            print(f"   结果: {'成功' if result['success'] else '失败'}")
            print(f"   耗时: {result.get('duration', 0):.1f}秒")
            
            if result["error"]:
                print(f"   错误: {result['error'][:200]}...")
            
            # 6. 提交结果
            print("\n5. 提交结果...")
            success = await executor.submit_result(
                task_id=task["task_id"],
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
        
        # 7. 关闭连接
        print("\n6. 关闭连接...")
        await executor.close()
        print("   ✅ 连接已关闭")
        
        print("\n" + "=" * 60)
        print("示例执行完成!")
        print("=" * 60)
        
        return True
        
    except ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        print("\n请确保:")
        print("1. CodeMCP 服务器正在运行")
        print("2. 服务器地址正确: ws://localhost:8000/mcp/ws/executor")
        print("3. 防火墙允许端口8000")
        return False
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def continuous_execution_example():
    """持续执行示例"""
    
    executor = CodeMCPExecutor(
        executor_id="continuous-executor",
        capabilities=["python", "pytest", "shell"]
    )
    
    print("🚀 进入持续执行模式...")
    print("🛑 按 Ctrl+C 停止")
    
    try:
        await executor.connect()
        
        completed = 0
        failed = 0
        
        while True:
            # 获取任务
            task = await executor.fetch_task()
            
            if task:
                print(f"\n📥 获取到任务: {task.get('task_id')}")
                
                # 执行任务
                result = await executor.execute_task(task)
                
                # 提交结果
                success = await executor.submit_result(
                    task_id=task["task_id"],
                    success=result["success"],
                    output=result["output"],
                    error_message=result["error"],
                    duration=result.get("duration", 0)
                )
                
                if success and result["success"]:
                    completed += 1
                    print(f"✅ 任务完成 (总计: {completed} 成功, {failed} 失败)")
                else:
                    failed += 1
                    print(f"❌ 任务失败 (总计: {completed} 成功, {failed} 失败)")
                
                # 短暂休息
                await asyncio.sleep(1)
            else:
                # 没有任务，等待一段时间再重试
                print("⏳ 等待新任务...")
                await asyncio.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    finally:
        await executor.close()
        print("🔌 连接已关闭")
    
    print(f"\n🎉 持续执行完成")
    print(f"   成功: {completed}")
    print(f"   失败: {failed}")


if __name__ == "__main__":
    # 运行示例
    print("CodeMCP Executor 客户端库")
    print("=" * 60)
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        # 持续执行模式
        asyncio.run(continuous_execution_example())
    else:
        # 单次示例模式
        asyncio.run(example_usage())