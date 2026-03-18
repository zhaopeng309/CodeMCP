"""
HTTP客户端工具模块

提供与CodeMCP API交互的HTTP客户端。
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urljoin

import httpx
from rich.console import Console
from rich.table import Table

from ..config import settings
from .logging import get_logger

logger = get_logger(__name__)


class APIClient:
    """同步HTTP客户端"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            timeout: 请求超时时间
        """
        self.base_url = base_url or f"http://localhost:{settings.port}{settings.api_prefix}"
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers(),
            follow_redirects=True,
        )
        logger.info(f"初始化API客户端，基础URL: {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CodeMCP-CLI/1.0.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """处理HTTP响应"""
        # 检查状态码
        status_code = response.status_code
        
        # 如果是重定向状态码（3xx），不调用raise_for_status()，因为它会对3xx状态码引发异常
        # 注意：httpx的raise_for_status()实际上只对4xx和5xx状态码引发异常，
        # 但为了安全起见，我们单独处理3xx状态码
        if 300 <= status_code < 400:
            logger.warning(
                f"收到重定向响应 {status_code}，重定向到: {response.headers.get('location', '未知')}"
            )
            # 对于重定向响应，我们返回一个错误字典，而不是引发异常
            # 这样上层代码可以决定如何处理
            return {
                "error": "redirect",
                "status_code": status_code,
                "location": response.headers.get('location'),
                "message": f"重定向响应 '{status_code} {response.reason_phrase}' for url '{response.url}'"
            }
        
        # 对于非3xx状态码，正常处理
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            raise
    
    def get_tasks(
        self,
        feature_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取任务列表"""
        params: Dict[str, Union[str, int]] = {
            "page": page,
            "page_size": page_size,
        }
        if feature_id:
            params["feature_id"] = feature_id
        if status:
            params["status"] = status
        
        response = self.client.get("/tasks", params=params)
        return self._handle_response(response)
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取任务详情"""
        response = self.client.get(f"/tasks/{task_id}")
        return self._handle_response(response)
    
    def create_task(
        self,
        feature_id: str,
        command: str,
        description: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """创建新任务"""
        data = {
            "feature_id": feature_id,
            "command": command,
            "max_retries": max_retries,
            "timeout": timeout,
            "priority": priority,
        }
        if description:
            data["description"] = description
        
        response = self.client.post("/tasks", json=data)
        return self._handle_response(response)
    
    def update_task(
        self,
        task_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """更新任务"""
        response = self.client.put(f"/tasks/{task_id}", json=kwargs)
        return self._handle_response(response)
    
    def delete_task(self, task_id: str) -> None:
        """删除任务"""
        response = self.client.delete(f"/tasks/{task_id}")
        self._handle_response(response)
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """执行任务"""
        response = self.client.post(f"/tasks/{task_id}/execute", json={})
        return self._handle_response(response)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        response = self.client.get(f"/tasks/status/{task_id}")
        return self._handle_response(response)
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        response = self.client.post(f"/tasks/{task_id}/cancel")
        return self._handle_response(response)
    
    def get_next_task(self) -> Dict[str, Any]:
        """获取下一个待执行任务"""
        response = self.client.get("/tasks/next")
        return self._handle_response(response)
    
    def get_features(
        self,
        system_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取功能点列表"""
        params: Dict[str, Union[str, int]] = {
            "page": page,
            "page_size": page_size,
        }
        if system_id:
            params["system_id"] = system_id
        
        response = self.client.get("/features", params=params)
        return self._handle_response(response)
    
    def get_systems(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取系统列表"""
        params = {
            "page": page,
            "page_size": page_size,
        }
        response = self.client.get("/systems", params=params)
        return self._handle_response(response)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        response = self.client.get("/queue/status")
        return self._handle_response(response)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        response = self.client.get("/status/")
        return self._handle_response(response)
    
    def close(self):
        """关闭客户端"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncAPIClient:
    """异步HTTP客户端"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        初始化异步API客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            timeout: 请求超时时间
        """
        self.base_url = base_url or f"http://localhost:{settings.port}{settings.api_prefix}"
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers(),
            follow_redirects=True,
        )
        logger.info(f"初始化异步API客户端，基础URL: {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CodeMCP-CLI/1.0.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """处理HTTP响应"""
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            raise
    
    async def get_tasks(
        self,
        feature_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取任务列表"""
        params: Dict[str, Union[str, int]] = {
            "page": page,
            "page_size": page_size,
        }
        if feature_id:
            params["feature_id"] = feature_id
        if status:
            params["status"] = status
        
        response = await self.client.get("/tasks", params=params)
        return await self._handle_response(response)
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取任务详情"""
        response = await self.client.get(f"/tasks/{task_id}")
        return await self._handle_response(response)
    
    async def create_task(
        self,
        feature_id: str,
        command: str,
        description: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """创建新任务"""
        data = {
            "feature_id": feature_id,
            "command": command,
            "max_retries": max_retries,
            "timeout": timeout,
            "priority": priority,
        }
        if description:
            data["description"] = description
        
        response = await self.client.post("/tasks", json=data)
        return await self._handle_response(response)
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class CLIFormatter:
    """CLI输出格式化工具"""
    
    def __init__(self):
        self.console = Console()
    
    def format_task_table(self, tasks: List[Dict[str, Any]]) -> Table:
        """格式化任务列表为表格"""
        table = Table(title="任务列表", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=36)
        table.add_column("功能点", width=20)
        table.add_column("命令", width=40)
        table.add_column("状态", justify="right")
        table.add_column("创建时间", justify="right")
        
        for task in tasks:
            task_id = task.get("id", "")[:8] + "..."
            feature_name = task.get("feature", {}).get("name", "未知")[:18] + "..."
            command = task.get("command", "")[:37] + "..."
            status = task.get("status", "unknown")
            created_at = task.get("created_at", "")[:16]
            
            # 状态颜色
            status_style = "green"
            if status == "failed":
                status_style = "red"
            elif status == "running":
                status_style = "yellow"
            elif status == "pending":
                status_style = "blue"
            
            table.add_row(
                task_id,
                feature_name,
                command,
                f"[{status_style}]{status}[/{status_style}]",
                created_at,
            )
        
        return table
    
    def format_task_detail(self, task: Dict[str, Any]) -> Table:
        """格式化任务详情为表格"""
        table = Table(title=f"任务详情 - {task.get('id', '未知')}", show_header=False)
        
        table.add_row("ID", task.get("id", ""))
        table.add_row("功能点", task.get("feature", {}).get("name", "未知"))
        table.add_row("系统", task.get("feature", {}).get("system", {}).get("name", "未知"))
        table.add_row("命令", task.get("command", ""))
        table.add_row("描述", task.get("description", "无"))
        
        # 状态
        status = task.get("status", "unknown")
        status_style = "green"
        if status == "failed":
            status_style = "red"
        elif status == "running":
            status_style = "yellow"
        elif status == "pending":
            status_style = "blue"
        
        table.add_row("状态", f"[{status_style}]{status}[/{status_style}]")
        table.add_row("优先级", str(task.get("priority", 0)))
        table.add_row("最大重试次数", str(task.get("max_retries", 3)))
        table.add_row("当前重试次数", str(task.get("retry_count", 0)))
        table.add_row("超时时间", str(task.get("timeout", 3600)))
        table.add_row("创建时间", task.get("created_at", ""))
        table.add_row("开始时间", task.get("started_at", "未开始"))
        table.add_row("完成时间", task.get("completed_at", "未完成"))
        table.add_row("错误信息", task.get("error_message", "无"))
        
        return table
    
    def format_success_message(self, message: str) -> str:
        """格式化成功消息"""
        return f"[bold green]✓ {message}[/bold green]"
    
    def format_error_message(self, message: str) -> str:
        """格式化错误消息"""
        return f"[bold red]✗ {message}[/bold red]"
    
    def format_warning_message(self, message: str) -> str:
        """格式化警告消息"""
        return f"[bold yellow]⚠ {message}[/bold yellow]"
    
    def format_info_message(self, message: str) -> str:
        """格式化信息消息"""
        return f"[bold blue]ℹ {message}[/bold blue]"