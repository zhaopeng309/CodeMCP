"""
实时监控服务

监控任务执行状态、系统资源和性能指标。
"""

import asyncio
import logging
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db_session
from ..models.test import TestModel, TestStatus
from .task_engine import TaskEngine

logger = logging.getLogger(__name__)


class SystemMetrics:
    """系统指标收集器"""
    
    def __init__(self):
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.max_samples = 60  # 保留最近60个样本
    
    def collect(self) -> Dict[str, float]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_samples.append(cpu_percent)
            if len(self.cpu_samples) > self.max_samples:
                self.cpu_samples.pop(0)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_samples.append(memory_percent)
            if len(self.memory_samples) > self.max_samples:
                self.memory_samples.pop(0)
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 网络IO
            net_io = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_avg": sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
                "memory_percent": memory_percent,
                "memory_avg": sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0,
                "memory_total_gb": memory.total / (1024**3),
                "memory_used_gb": memory.used / (1024**3),
                "disk_percent": disk_percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_used_gb": disk.used / (1024**3),
                "net_bytes_sent": net_io.bytes_sent,
                "net_bytes_recv": net_io.bytes_recv,
                "timestamp": datetime.now().timestamp(),
            }
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return {
                "cpu_percent": 0,
                "cpu_avg": 0,
                "memory_percent": 0,
                "memory_avg": 0,
                "memory_total_gb": 0,
                "memory_used_gb": 0,
                "disk_percent": 0,
                "disk_total_gb": 0,
                "disk_used_gb": 0,
                "net_bytes_sent": 0,
                "net_bytes_recv": 0,
                "timestamp": datetime.now().timestamp(),
            }


class TaskMetrics:
    """任务指标收集器"""
    
    def __init__(self, task_engine: TaskEngine):
        self.task_engine = task_engine
        self.task_history: List[Dict] = []
        self.max_history = 1000
    
    async def collect(self, session: AsyncSession) -> Dict[str, Any]:
        """收集任务指标"""
        try:
            # 获取任务统计
            total_tasks = await self._count_tasks(session)
            tasks_by_status = await self._count_tasks_by_status(session)
            
            # 获取最近任务
            recent_tasks = await self._get_recent_tasks(session, limit=10)
            
            # 计算成功率
            success_rate = 0
            if tasks_by_status.get(TestStatus.PASSED, 0) + tasks_by_status.get(TestStatus.FAILED, 0) > 0:
                success_rate = tasks_by_status.get(TestStatus.PASSED, 0) / (
                    tasks_by_status.get(TestStatus.PASSED, 0) + tasks_by_status.get(TestStatus.FAILED, 0)
                ) * 100
            
            # 获取任务引擎状态
            engine_metrics = {
                "window_size": self.task_engine.task_window.size,
                "running_tasks": len(self.task_engine.running_tasks),
                "waiting_queue": len(self.task_engine.task_window.waiting_queue),
                "available_slots": self.task_engine.task_window.available_slots,
            }
            
            metrics = {
                "total_tasks": total_tasks,
                "tasks_by_status": {k.value: v for k, v in tasks_by_status.items()},
                "success_rate": round(success_rate, 2),
                "recent_tasks": recent_tasks,
                "engine_metrics": engine_metrics,
                "timestamp": datetime.now().timestamp(),
            }
            
            # 保存到历史
            self.task_history.append(metrics)
            if len(self.task_history) > self.max_history:
                self.task_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集任务指标失败: {e}")
            return {
                "total_tasks": 0,
                "tasks_by_status": {},
                "success_rate": 0,
                "recent_tasks": [],
                "engine_metrics": {},
                "timestamp": datetime.now().timestamp(),
            }
    
    async def _count_tasks(self, session: AsyncSession) -> int:
        """统计总任务数"""
        result = await session.execute(select(TestModel))
        return len(result.scalars().all())
    
    async def _count_tasks_by_status(self, session: AsyncSession) -> Dict[TestStatus, int]:
        """按状态统计任务数"""
        result = await session.execute(
            select(TestModel.status, TestModel.id)
        )
        rows = result.all()
        
        counts = {status: 0 for status in TestStatus}
        for status, _ in rows:
            if status in counts:
                counts[status] += 1
        
        return counts
    
    async def _get_recent_tasks(self, session: AsyncSession, limit: int = 10) -> List[Dict]:
        """获取最近任务"""
        result = await session.execute(
            select(TestModel)
            .order_by(TestModel.created_at.desc())
            .limit(limit)
        )
        tasks = result.scalars().all()
        
        return [
            {
                "id": task.id,
                "status": task.status.value,
                "command": task.command[:50] + "..." if len(task.command) > 50 else task.command,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "duration": task.duration,
                "exit_code": task.exit_code,
            }
            for task in tasks
        ]


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.execution_times: List[float] = []
        self.success_counts: List[bool] = []
        self.max_samples = 100
    
    def record_execution(self, duration: float, success: bool):
        """记录执行性能"""
        self.execution_times.append(duration)
        self.success_counts.append(success)
        
        if len(self.execution_times) > self.max_samples:
            self.execution_times.pop(0)
            self.success_counts.pop(0)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if not self.execution_times:
            return {
                "avg_execution_time": 0,
                "min_execution_time": 0,
                "max_execution_time": 0,
                "success_rate": 0,
                "total_executions": 0,
            }
        
        avg_time = sum(self.execution_times) / len(self.execution_times)
        min_time = min(self.execution_times) if self.execution_times else 0
        max_time = max(self.execution_times) if self.execution_times else 0
        
        success_rate = 0
        if self.success_counts:
            success_rate = sum(1 for s in self.success_counts if s) / len(self.success_counts) * 100
        
        return {
            "avg_execution_time": round(avg_time, 3),
            "min_execution_time": round(min_time, 3),
            "max_execution_time": round(max_time, 3),
            "success_rate": round(success_rate, 2),
            "total_executions": len(self.execution_times),
        }


class MonitorService:
    """监控服务"""
    
    def __init__(self, task_engine: TaskEngine):
        self.task_engine = task_engine
        self.system_metrics = SystemMetrics()
        self.task_metrics = TaskMetrics(task_engine)
        self.performance_metrics = PerformanceMetrics()
        
        self.metrics_history: List[Dict] = []
        self.max_history = 3600  # 保留1小时数据（假设每秒收集一次）
        
        self.running = False
        self.collection_interval = 5.0  # 收集间隔（秒）
    
    async def start(self):
        """启动监控服务"""
        if self.running:
            return
        
        self.running = True
        logger.info("监控服务已启动")
        
        # 启动收集循环
        asyncio.create_task(self._collection_loop())
    
    async def stop(self):
        """停止监控服务"""
        self.running = False
        logger.info("监控服务已停止")
    
    async def _collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指标收集循环错误: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def collect_metrics(self):
        """收集所有指标"""
        try:
            # 收集系统指标
            system_data = self.system_metrics.collect()
            
            # 收集任务指标
            async for session in get_db_session():
                task_data = await self.task_metrics.collect(session)
                break
            
            # 收集性能指标
            performance_data = self.performance_metrics.get_metrics()
            
            # 合并指标
            metrics = {
                "system": system_data,
                "tasks": task_data,
                "performance": performance_data,
                "timestamp": datetime.now().isoformat(),
            }
            
            # 保存到历史
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集监控指标失败: {e}")
            return None
    
    def get_current_metrics(self) -> Optional[Dict]:
        """获取当前指标"""
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def get_metrics_history(self, limit: int = 100) -> List[Dict]:
        """获取指标历史"""
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def get_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        current = self.get_current_metrics()
        if not current:
            return {"status": "no_data"}
        
        system = current.get("system", {})
        tasks = current.get("tasks", {})
        performance = current.get("performance", {})
        
        return {
            "status": "healthy",
            "system": {
                "cpu": f"{system.get('cpu_percent', 0):.1f}%",
                "memory": f"{system.get('memory_percent', 0):.1f}%",
                "disk": f"{system.get('disk_percent', 0):.1f}%",
            },
            "tasks": {
                "total": tasks.get("total_tasks", 0),
                "running": tasks.get("engine_metrics", {}).get("running_tasks", 0),
                "waiting": tasks.get("engine_metrics", {}).get("waiting_queue", 0),
                "success_rate": f"{tasks.get('success_rate', 0):.1f}%",
            },
            "performance": {
                "avg_time": f"{performance.get('avg_execution_time', 0):.3f}s",
                "success_rate": f"{performance.get('success_rate', 0):.1f}%",
            },
            "timestamp": current.get("timestamp"),
        }
    
    def record_task_execution(self, duration: float, success: bool):
        """记录任务执行性能"""
        self.performance_metrics.record_execution(duration, success)


# 全局监控服务实例
_monitor_service: Optional[MonitorService] = None


def get_monitor_service(task_engine: Optional[TaskEngine] = None) -> Optional[MonitorService]:
    """获取监控服务实例"""
    global _monitor_service
    if _monitor_service is None and task_engine is not None:
        _monitor_service = MonitorService(task_engine)
    return _monitor_service


async def start_monitoring(task_engine: TaskEngine):
    """启动监控"""
    monitor = get_monitor_service(task_engine)
    if monitor:
        await monitor.start()


async def stop_monitoring():
    """停止监控"""
    monitor = get_monitor_service()
    if monitor:
        await monitor.stop()