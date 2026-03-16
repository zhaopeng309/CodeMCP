# 任务窗口化执行机制

## 概述
任务窗口化执行机制是 CodeMCP 的核心特性之一，它通过限制同时执行的任务数量（窗口大小），确保系统资源得到合理利用，同时提供任务优先级管理和失败处理能力。

## 设计原理

### 窗口化执行概念
```
执行窗口（深度=5）
┌───┬───┬───┬───┬───┐
│ 1 │ 2 │ 3 │ 4 │ 5 │  ← 窗口位置
├───┼───┼───┼───┼───┤
│ ● │ ● │ ● │ ○ │ ○ │  ← 任务状态（●=执行中，○=空闲）
└───┴───┴───┴───┴───┘
     ↑
     窗口已用：3/5

任务队列
┌───┬───┬───┬───┬───┬───┐
│ 6 │ 7 │ 8 │ 9 │10 │...│  ← 待执行任务（按优先级排序）
└───┴───┴───┴───┴───┴───┘
```

### 核心特性
1. **滑动窗口**: 任务完成后，窗口向前滑动，新任务进入窗口
2. **优先级调度**: 高优先级任务优先进入窗口
3. **资源限制**: 防止系统过载
4. **失败隔离**: 失败任务不会阻塞整个窗口
5. **实时监控**: 窗口状态实时可见

## 窗口管理器实现

### WindowManager 类
```python
# src/codemcp/core/task_window.py
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import heapq

from sqlalchemy.orm import Session

from ..models.feature import Feature
from ..utils.logging import get_logger


class WindowSlotStatus(Enum):
    """窗口槽位状态"""
    EMPTY = "empty"
    RESERVED = "reserved"  # 已预留但未开始执行
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WindowSlot:
    """窗口槽位"""
    slot_id: int  # 1-based
    feature_id: Optional[int] = None
    feature: Optional[Feature] = None
    status: WindowSlotStatus = WindowSlotStatus.EMPTY
    reserved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    executor_id: Optional[str] = None
    task_future: Optional[asyncio.Future] = None
    
    @property
    def is_available(self) -> bool:
        """槽位是否可用"""
        return self.status in [WindowSlotStatus.EMPTY, WindowSlotStatus.COMPLETED, WindowSlotStatus.FAILED]
    
    @property
    def duration(self) -> Optional[float]:
        """执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class WindowConfig:
    """窗口配置"""
    size: int = 5  # 窗口大小
    max_reservation_time: int = 300  # 最大预留时间（秒）
    priority_weights: Dict[str, float] = field(default_factory=lambda: {
        "priority": 0.6,      # 任务优先级权重
        "waiting_time": 0.3,  # 等待时间权重
        "retry_count": 0.1,   # 重试次数权重（负权重）
    })
    cleanup_interval: int = 60  # 清理间隔（秒）


class WindowManager:
    """窗口管理器"""
    
    def __init__(self, db: Session, config: Optional[WindowConfig] = None):
        self.db = db
        self.config = config or WindowConfig()
        self.logger = get_logger(__name__)
        
        # 初始化窗口槽位
        self.slots: Dict[int, WindowSlot] = {
            i: WindowSlot(slot_id=i)
            for i in range(1, self.config.size + 1)
        }
        
        # 任务队列（最小堆，按分数排序）
        self.task_queue: List[Tuple[float, int, Feature]] = []  # (score, timestamp, feature)
        self.task_timestamps: Dict[int, datetime] = {}  # feature_id -> 入队时间
        
        # 锁和事件
        self._lock = asyncio.Lock()
        self._window_changed = asyncio.Event()
        
        # 统计信息
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration": 0.0,
            "window_utilization": 0.0,
        }
    
    async def start(self) -> None:
        """启动窗口管理器"""
        self.logger.info(f"窗口管理器启动，窗口大小: {self.config.size}")
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_task())
        
        # 启动统计任务
        asyncio.create_task(self._stats_task())
    
    async def stop(self) -> None:
        """停止窗口管理器"""
        self.logger.info("窗口管理器停止")
    
    async def add_task(self, feature: Feature) -> bool:
        """添加任务到队列"""
        async with self._lock:
            # 检查任务是否已在队列或窗口中
            if self._is_task_in_system(feature.id):
                self.logger.warning(f"任务 {feature.id} 已在系统中")
                return False
            
            # 计算任务分数
            score = self._calculate_task_score(feature)
            timestamp = datetime.utcnow()
            
            # 添加到优先队列
            heapq.heappush(self.task_queue, (-score, timestamp.timestamp(), feature))
            self.task_timestamps[feature.id] = timestamp
            
            self.logger.info(f"任务添加到队列: {feature.id} ({feature.name}), 分数: {score:.2f}")
            
            # 触发窗口更新
            self._window_changed.set()
            
            return True
    
    async def reserve_slot(self, feature: Feature, executor_id: str) -> Optional[int]:
        """为任务预留窗口槽位"""
        async with self._lock:
            # 查找可用槽位
            available_slots = [
                slot for slot in self.slots.values()
                if slot.is_available
            ]
            
            if not available_slots:
                self.logger.debug("无可用窗口槽位")
                return None
            
            # 选择第一个可用槽位
            slot = available_slots[0]
            
            # 预留槽位
            slot.feature_id = feature.id
            slot.feature = feature
            slot.status = WindowSlotStatus.RESERVED
            slot.reserved_at = datetime.utcnow()
            slot.executor_id = executor_id
            
            self.logger.info(
                f"槽位预留: 槽位 {slot.slot_id} -> 任务 {feature.id} "
                f"({feature.name}), 执行者: {executor_id}"
            )
            
            # 更新统计
            self._update_stats()
            
            return slot.slot_id
    
    async def start_execution(self, slot_id: int) -> bool:
        """开始执行槽位中的任务"""
        async with self._lock:
            slot = self.slots.get(slot_id)
            if not slot or slot.status != WindowSlotStatus.RESERVED:
                self.logger.warning(f"槽位 {slot_id} 不可用于开始执行")
                return False
            
            # 更新状态
            slot.status = WindowSlotStatus.RUNNING
            slot.started_at = datetime.utcnow()
            
            # 更新数据库中的任务状态
            if slot.feature:
                slot.feature.mark_as_started()
                self.db.commit()
            
            self.logger.info(f"任务开始执行: 槽位 {slot_id}, 任务 {slot.feature_id}")
            
            # 创建任务Future
            slot.task_future = asyncio.Future()
            
            return True
    
    async def complete_execution(
        self,
        slot_id: int,
        success: bool,
        exit_code: int = None,
        stdout: str = None,
        stderr: str = None,
        duration: float = None
    ) -> bool:
        """完成槽位中的任务执行"""
        async with self._lock:
            slot = self.slots.get(slot_id)
            if not slot or slot.status != WindowSlotStatus.RUNNING:
                self.logger.warning(f"槽位 {slot_id} 未在运行中")
                return False
            
            # 更新槽位状态
            slot.status = WindowSlotStatus.COMPLETED if success else WindowSlotStatus.FAILED
            slot.completed_at = datetime.utcnow()
            
            # 更新数据库中的任务状态
            if slot.feature:
                slot.feature.mark_as_completed(success, duration)
                
                # 创建测试记录
                from ..models.test import Test
                test = Test(
                    feature_id=slot.feature.id,
                    command=slot.feature.test_command,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration=duration,
                    status="passed" if success else "failed",
                    started_at=slot.started_at,
                    completed_at=slot.completed_at
                )
                self.db.add(test)
                self.db.commit()
            
            # 更新统计
            self.stats["total_processed"] += 1
            if success:
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
            
            # 计算平均时长
            if duration:
                total = self.stats["avg_duration"] * (self.stats["total_processed"] - 1)
                self.stats["avg_duration"] = (total + duration) / self.stats["total_processed"]
            
            self.logger.info(
                f"任务完成: 槽位 {slot_id}, 任务 {slot.feature_id}, "
                f"结果: {'成功' if success else '失败'}, 时长: {duration:.2f}s"
            )
            
            # 触发任务Future
            if slot.task_future and not slot.task_future.done():
                slot.task_future.set_result({
                    "success": success,
                    "duration": duration,
                    "exit_code": exit_code
                })
            
            # 清理槽位（延迟清理）
            asyncio.create_task(self._cleanup_slot(slot_id))
            
            # 触发窗口更新
            self._window_changed.set()
            
            return True
    
    async def get_available_slots(self) -> List[Dict]:
        """获取可用槽位信息"""
        async with self._lock:
            return [
                {
                    "slot_id": slot.slot_id,
                    "status": slot.status.value,
                    "feature_id": slot.feature_id,
                    "feature_name": slot.feature.name if slot.feature else None,
                    "executor_id": slot.executor_id,
                    "duration": slot.duration,
                    "reserved_at": slot.reserved_at.isoformat() if slot.reserved_at else None,
                    "started_at": slot.started_at.isoformat() if slot.started_at else None,
                    "completed_at": slot.completed_at.isoformat() if slot.completed_at else None,
                }
                for slot in self.slots.values()
            ]
    
    async def get_queue_status(self) -> Dict:
        """获取队列状态"""
        async with self._lock:
            return {
                "queue_size": len(self.task_queue),
                "window_size": self.config.size,
                "window_used": sum(1 for s in self.slots.values() if not s.is_available),
                "window_utilization": self.stats["window_utilization"],
                "stats": self.stats.copy(),
                "slots": await self.get_available_slots(),
            }
    
    def _calculate_task_score(self, feature: Feature) -> float:
        """计算任务调度分数"""
        weights = self.config.priority_weights
        
        # 1. 优先级分数（越高越好）
        priority_score = (10 - min(feature.priority, 10)) / 10  # 归一化到 0-1
        
        # 2. 等待时间分数（等待越久分数越高）
        if feature.id in self.task_timestamps:
            wait_time = (datetime.utcnow() - self.task_timestamps[feature.id]).total_seconds()
            max_wait = 3600  # 1小时
            waiting_score = min(wait_time / max_wait, 1.0)
        else:
            waiting_score = 0.0
        
        # 3. 重试次数分数（重试越多分数越低）
        retry_score = max(0, 1.0 - (feature.retry_count / feature.max_retries))
        
        # 加权总分
        total_score = (
            weights.get("priority", 0.6) * priority_score +
            weights.get("waiting_time", 0.3) * waiting_score +
            weights.get("retry_count", 0.1) * retry_score
        )
        
        return total_score
    
    def _is_task_in_system(self, feature_id: int) -> bool:
        """检查任务是否已在系统（队列或窗口）中"""
        # 检查队列
        for _, _, feature in self.task_queue:
            if feature.id == feature_id:
                return True
        
        # 检查窗口
        for slot in self.slots.values():
            if slot.feature_id == feature_id:
                return True
        
        return False
    
    def _update_stats(self) -> None:
        """更新统计信息"""
        used_slots = sum(1 for s in self.slots.values() if not s.is_available)
        self.stats["window_utilization"] = used_slots / self.config.size
    
    async def _cleanup_slot(self, slot_id: int, delay: float = 2.0) -> None:
        """清理槽位（延迟执行）"""
        await asyncio.sleep(delay)
        
        async with self._lock:
            slot = self.slots.get(slot_id)
            if slot and slot.status in [WindowSlotStatus.COMPLETED, WindowSlotStatus.FAILED]:
                # 重置槽位
                self.slots[slot_id] = WindowSlot(slot_id=slot_id)
                self.logger.debug(f"槽位清理完成: {slot_id}")
    
    async def _cleanup_task(self) -> None:
        """定期清理任务"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                
                async with self._lock:
                    now = datetime.utcnow()
                    cleaned = 0
                    
                    # 清理过期的预留槽位
                    for slot in self.slots.values():
                        if (slot.status == WindowSlotStatus.RESERVED and 
                            slot.reserved_at and
                            (now - slot.reserved_at).total_seconds() > self.config.max_reservation_time):
                            
                            self.logger.warning(
                                f"槽位预留过期: 槽位 {slot.slot_id}, 任务 {slot.feature_id}"
                            )
                            self.slots[slot.slot_id] = WindowSlot(slot_id=slot.slot_id)
                            cleaned += 1
                    
                    if cleaned > 0:
                        self.logger.info(f"清理了 {cleaned} 个过期槽位")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理任务错误: {e}", exc_info=True)
    
    async def _stats_task(self) -> None:
        """定期更新统计信息"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒更新一次
                self._update_stats()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"统计任务错误: {e}", exc_info=True)
```

## 窗口调度算法

### 调度流程
```python
# src/codemcp/core/window_scheduler.py
from typing import List, Optional
import asyncio

from .task_window import WindowManager
from ..models.feature import Feature


class WindowScheduler:
    """窗口调度器"""
    
    def __init__(self, window_manager: WindowManager):
        self.wm = window_manager
        self.logger = get_logger(__name__)
    
    async def schedule_next_batch(self) -> List[Feature]:
        """调度下一批任务到窗口"""
        scheduled = []
        
        # 获取当前窗口状态
        window_status = await self.wm.get_queue_status()
        available_slots = window_status["window_size"] - window_status["window_used"]
        
        if available_slots <= 0:
            return scheduled
        
        # 从队列中获取任务
        tasks_to_schedule = await self._select_tasks_for_window(available_slots)
        
        for feature in tasks_to_schedule:
            # 尝试调度任务
            if await self._schedule_task(feature):
                scheduled.append(feature)
        
        if scheduled:
            self.logger.info(f"调度了 {len(scheduled)} 个任务到窗口")
        
        return scheduled
    
    async def _select_tasks_for_window(self, count: int) -> List[Feature]:
        """选择要调度到窗口的任务"""
        # 这里可以实现更复杂的选择逻辑
        # 例如：考虑系统负载、任务依赖关系等
        
        # 简单实现：按分数选择前N个任务
        selected = []
        
        # 获取所有待调度任务
        all_tasks = await self._get_pending_tasks()
        
        # 按分数排序
        sorted_tasks = sorted(
            all_tasks,
            key=lambda f: self.wm._calculate_task_score(f),
            reverse=True
        )
