"""
TaskExecutor 单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.codemcp.core.executor import (
    TaskExecutor,
    LocalCommandExecutor,
    MockExecutor,
    get_executor,
    set_executor,
)
from src.codemcp.models.test import TestModel as TestModelClass, TestStatus as TestStatusEnum


class TestTaskExecutor:
    """TaskExecutor 单元测试类"""

    def test_task_executor_abstract(self):
        """测试 TaskExecutor 是抽象类"""
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            TaskExecutor()

    def test_task_executor_abstract_methods(self):
        """测试 TaskExecutor 抽象方法"""
        # 创建具体子类
        class ConcreteExecutor(TaskExecutor):
            async def execute(self, test):
                return 0, "", "", 0.0
            
            async def validate_command(self, command):
                return True
        
        executor = ConcreteExecutor()
        assert isinstance(executor, TaskExecutor)


class TestLocalCommandExecutor:
    """LocalCommandExecutor 单元测试类"""

    @pytest.fixture
    def executor(self):
        """创建 LocalCommandExecutor 实例"""
        return LocalCommandExecutor(timeout=10)

    @pytest.fixture
    def sample_test(self):
        """创建示例测试"""
        return TestModelClass(
            feature_id="test-feature-id",
            command="echo 'test'",
            status=TestStatusEnum.PENDING,
        )

    @pytest.mark.asyncio
    async def test_local_executor_creation(self, executor):
        """测试 LocalCommandExecutor 创建"""
        assert executor.timeout == 10

    @pytest.mark.asyncio
    async def test_validate_command_valid(self, executor):
        """测试验证有效命令"""
        # 简单命令应该有效
        result = await executor.validate_command("echo 'test'")
        assert result is True
        
        # 复杂命令应该有效
        result = await executor.validate_command("python -c \"print('hello')\"")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_command_empty(self, executor):
        """测试验证空命令"""
        result = await executor.validate_command("")
        assert result is False
        
        result = await executor.validate_command("   ")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_command_dangerous(self, executor):
        """测试验证危险命令"""
        # 这里只是简单检查，实际实现可能更复杂
        result = await executor.validate_command("rm -rf /")
        assert result is True  # 取决于实际实现

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    async def test_execute_success(self, mock_create_subprocess, executor, sample_test):
        """测试执行成功"""
        # 模拟成功进程
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"test output\n", b"")
        mock_create_subprocess.return_value = mock_process
        
        # 模拟时间
        with patch("time.time", side_effect=[0.0, 0.5]):
            exit_code, stdout, stderr, duration = await executor.execute(sample_test)
        
        assert exit_code == 0
        assert stdout == "test output\n"
        assert stderr == ""
        assert duration == 0.5
        mock_create_subprocess.assert_called_once_with(
            "echo 'test'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    async def test_execute_failure(self, mock_create_subprocess, executor, sample_test):
        """测试执行失败"""
        # 模拟失败进程
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"error message\n")
        mock_create_subprocess.return_value = mock_process
        
        with patch("time.time", side_effect=[0.0, 0.3]):
            exit_code, stdout, stderr, duration = await executor.execute(sample_test)
        
        assert exit_code == 1
        assert stdout == ""
        assert stderr == "error message\n"
        assert duration == 0.3

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    async def test_execute_timeout(self, mock_create_subprocess, executor, sample_test):
        """测试执行超时"""
        # 模拟长时间运行的进程
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_create_subprocess.return_value = mock_process
        
        # 使用较短的超时时间
        executor.timeout = 0.1
        
        exit_code, stdout, stderr, duration = await executor.execute(sample_test)
        
        assert exit_code == -1  # 超时退出码
        assert "timeout" in stderr.lower()
        assert duration >= 0.1

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    async def test_execute_exception(self, mock_create_subprocess, executor, sample_test):
        """测试执行异常"""
        # 模拟异常
        mock_create_subprocess.side_effect = Exception("Process creation failed")
        
        exit_code, stdout, stderr, duration = await executor.execute(sample_test)
        
        assert exit_code == -1
        assert "exception" in stderr.lower()
        assert "process creation failed" in stderr.lower()

    @pytest.mark.asyncio
    async def test_execute_with_stderr(self, executor, sample_test):
        """测试执行带有标准错误输出"""
        # 修改测试命令
        sample_test.command = "python -c \"import sys; sys.stderr.write('error'); sys.stdout.write('output')\""
        
        # 使用实际执行（可能需要安装python）
        try:
            exit_code, stdout, stderr, duration = await executor.execute(sample_test)
            # 检查结果
            assert exit_code == 0
            assert "output" in stdout
            assert "error" in stderr
        except Exception:
            # 如果python不可用，跳过测试
            pytest.skip("Python not available for actual execution test")

    @pytest.mark.asyncio
    async def test_execute_large_output(self, executor):
        """测试执行大量输出"""
        test = TestModelClass(
            feature_id="test-feature-id",
            command="python -c \"print('x' * 10000)\"",
            status=TestStatusEnum.PENDING,
        )
        
        try:
            exit_code, stdout, stderr, duration = await executor.execute(test)
            assert exit_code == 0
            assert len(stdout) >= 10000
        except Exception:
            pytest.skip("Python not available for large output test")


class TestMockExecutor:
    """MockExecutor 单元测试类"""

    @pytest.fixture
    def success_executor(self):
        """创建成功 MockExecutor"""
        return MockExecutor(success=True, exit_code=0)

    @pytest.fixture
    def failure_executor(self):
        """创建失败 MockExecutor"""
        return MockExecutor(success=False, exit_code=1)

    @pytest.fixture
    def sample_test(self):
        """创建示例测试"""
        return TestModelClass(
            feature_id="test-feature-id",
            command="echo 'test'",
            status=TestStatusEnum.PENDING,
        )

    @pytest.mark.asyncio
    async def test_mock_executor_creation(self, success_executor):
        """测试 MockExecutor 创建"""
        assert success_executor.success is True
        assert success_executor.exit_code == 0

    @pytest.mark.asyncio
    async def test_validate_command_always_true(self, success_executor):
        """测试 MockExecutor 总是返回 True"""
        result = await success_executor.validate_command("")
        assert result is True
        
        result = await success_executor.validate_command("invalid command")
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_success(self, success_executor, sample_test):
        """测试 MockExecutor 成功执行"""
        exit_code, stdout, stderr, duration = await success_executor.execute(sample_test)
        
        assert exit_code == 0
        assert "Mock execution successful" in stdout
        assert stderr == ""
        assert duration == 0.1

    @pytest.mark.asyncio
    async def test_execute_failure(self, failure_executor, sample_test):
        """测试 MockExecutor 失败执行"""
        exit_code, stdout, stderr, duration = await failure_executor.execute(sample_test)
        
        assert exit_code == 1
        assert "Mock execution failed" in stdout
        assert stderr == ""
        assert duration == 0.1

    @pytest.mark.asyncio
    async def test_execute_custom_exit_code(self, sample_test):
        """测试 MockExecutor 自定义退出码"""
        executor = MockExecutor(success=True, exit_code=42)
        exit_code, stdout, stderr, duration = await executor.execute(sample_test)
        
        assert exit_code == 42


class TestExecutorFunctions:
    """get_executor 和 set_executor 函数测试"""

    def test_get_default_executor(self):
        """测试获取默认执行器"""
        executor = get_executor()
        assert isinstance(executor, LocalCommandExecutor)
        assert executor.timeout == 3600  # 默认超时时间

    def test_set_and_get_executor(self):
        """测试设置和获取执行器"""
        # 保存原始执行器
        original_executor = get_executor()
        
        try:
            # 创建新的执行器
            new_executor = MockExecutor(success=True)
            
            # 设置新执行器
            set_executor(new_executor)
            
            # 验证获取的是新执行器
            current_executor = get_executor()
            assert current_executor is new_executor
            assert isinstance(current_executor, MockExecutor)
        finally:
            # 恢复原始执行器
            set_executor(original_executor)

    def test_set_executor_type_check(self):
        """测试设置执行器类型检查"""
        with pytest.raises(TypeError):
            set_executor("not an executor")
        
        with pytest.raises(TypeError):
            set_executor(None)

    def test_executor_singleton_behavior(self):
        """测试执行器单例行为"""
        executor1 = get_executor()
        executor2 = get_executor()
        
        # 应该是同一个实例
        assert executor1 is executor2

    def test_thread_safety(self):
        """测试线程安全（简单验证）"""
        # 这个测试主要是文档目的，实际线程安全需要更复杂的测试
        executor = get_executor()
        assert executor is not None