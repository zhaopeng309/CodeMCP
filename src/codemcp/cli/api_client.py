"""
CLI API客户端管理器

提供CLI命令与真实API集成的客户端管理功能。
"""

import sys
from typing import Optional, Dict, Any
from contextlib import contextmanager

from rich.console import Console

from ..utils.http_client import APIClient, CLIFormatter
from .config import get_config
from ..exceptions import ConfigurationError

console = Console()
formatter = CLIFormatter()


class APIClientManager:
    """API客户端管理器"""
    
    def __init__(self):
        self.config = get_config()
        self._client: Optional[APIClient] = None
    
    @property
    def client(self) -> APIClient:
        """获取API客户端实例"""
        if self._client is None:
            self._client = self.create_client()
        return self._client
    
    def create_client(self) -> APIClient:
        """创建API客户端"""
        base_url = self.config.get("api.base_url", "http://localhost:8000")
        api_prefix = self.config.get("api.api_prefix", "/api/v1")
        timeout = self.config.get("api.timeout", 30.0)
        api_key = self.config.get("auth.token")
        
        # 构建完整的API URL
        full_url = f"{base_url}{api_prefix}"
        
        return APIClient(
            base_url=full_url,
            api_key=api_key,
            timeout=timeout,
        )
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            with self.create_client() as client:
                # 尝试获取系统状态
                response = client.get_system_status()
                console.print(formatter.format_success_message("API连接成功"))
                console.print(f"  服务器版本: {response.get('version', '未知')}")
                console.print(f"  运行状态: {response.get('status', '未知')}")
                return True
        except Exception as e:
            console.print(formatter.format_error_message(f"API连接失败: {e}"))
            console.print("请检查:")
            console.print("  1. API服务器是否正在运行")
            console.print("  2. 配置中的base_url是否正确")
            console.print("  3. 网络连接是否正常")
            return False
    
    def get_tasks_with_fallback(self, **kwargs) -> Dict[str, Any]:
        """获取任务列表，失败时返回模拟数据"""
        try:
            return self.client.get_tasks(**kwargs)
        except Exception as e:
            console.print(formatter.format_warning_message(f"获取任务列表失败，使用模拟数据: {e}"))
            return self._get_mock_tasks()
    
    def get_task_with_fallback(self, task_id: str) -> Dict[str, Any]:
        """获取任务详情，失败时返回模拟数据"""
        try:
            return self.client.get_task(task_id)
        except Exception as e:
            console.print(formatter.format_warning_message(f"获取任务详情失败，使用模拟数据: {e}"))
            return self._get_mock_task(task_id)
    
    def create_task_with_fallback(self, **kwargs) -> Dict[str, Any]:
        """创建任务，失败时返回模拟响应"""
        try:
            return self.client.create_task(**kwargs)
        except Exception as e:
            console.print(formatter.format_warning_message(f"创建任务失败，使用模拟响应: {e}"))
            return self._get_mock_create_response(**kwargs)
    
    def _get_mock_tasks(self) -> Dict[str, Any]:
        """获取模拟任务列表"""
        return {
            "tests": [
                {
                    "id": "mock-task-1",
                    "feature": {
                        "name": "用户认证",
                        "system": {"name": "用户管理系统"}
                    },
                    "command": "pytest tests/test_auth.py::test_login -xvs",
                    "status": "completed",
                    "created_at": "2026-03-15T10:00:00",
                    "priority": 0,
                    "max_retries": 3,
                    "retry_count": 0,
                },
                {
                    "id": "mock-task-2",
                    "feature": {
                        "name": "订单处理",
                        "system": {"name": "电商系统"}
                    },
                    "command": "pytest tests/test_order.py -xvs",
                    "status": "running",
                    "created_at": "2026-03-15T10:05:00",
                    "priority": 1,
                    "max_retries": 3,
                    "retry_count": 0,
                },
            ],
            "total": 2,
        }
    
    def _get_mock_task(self, task_id: str) -> Dict[str, Any]:
        """获取模拟任务详情"""
        return {
            "id": task_id,
            "feature": {
                "name": "用户认证",
                "system": {"name": "用户管理系统"}
            },
            "command": "pytest tests/test_auth.py::test_login -xvs",
            "description": "测试用户登录功能",
            "status": "completed",
            "priority": 0,
            "max_retries": 3,
            "retry_count": 0,
            "timeout": 3600,
            "created_at": "2026-03-15T10:00:00",
            "started_at": "2026-03-15T10:00:05",
            "completed_at": "2026-03-15T10:00:45",
            "error_message": None,
        }
    
    def _get_mock_create_response(self, **kwargs) -> Dict[str, Any]:
        """获取模拟创建响应"""
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "feature_id": kwargs.get("feature_id", ""),
            "command": kwargs.get("command", ""),
            "description": kwargs.get("description", ""),
            "status": "pending",
            "priority": kwargs.get("priority", 0),
            "max_retries": kwargs.get("max_retries", 3),
            "retry_count": 0,
            "timeout": kwargs.get("timeout", 3600),
            "created_at": "2026-03-15T10:00:00",
        }


@contextmanager
def api_client_context():
    """API客户端上下文管理器"""
    manager = APIClientManager()
    client = manager.client
    try:
        yield manager
    finally:
        client.close()


def require_api_connection(func):
    """装饰器：要求API连接"""
    def wrapper(*args, **kwargs):
        manager = APIClientManager()
        if not manager.test_connection():
            console.print(formatter.format_error_message("无法连接到API服务器"))
            console.print("请先启动API服务器或检查配置")
            sys.exit(1)
        return func(*args, **kwargs)
    return wrapper


# 全局管理器实例
_manager_instance: Optional[APIClientManager] = None


def get_api_manager() -> APIClientManager:
    """获取全局API管理器实例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = APIClientManager()
    return _manager_instance