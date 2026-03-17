---
name: codemcp-executor
description: "CodeMCP Executor Skill - AI协同编程的执行器，负责从CodeMCP服务器获取任务、执行功能实现、运行测试验证、提交执行结果。支持自动任务轮询、错误重试、智能问题修复，是CodeMCP多AI agent协作系统的核心执行者。"
metadata:
  {
    "openclaw": {
      "emoji": "⚡",
      "version": "1.0.0",
      "author": "OpenClaw AI",
      "license": "MIT",
      "requires": {
        "anyBins": ["git", "python3", "pytest"],
        "anyFiles": []
      },
      "recommends": {
        "skills": ["coding-agent", "codemcp-planner"]
      },
      "tags": ["codemcp", "executor", "ai-development", "task-execution", "testing-automation", "code-implementation"]
    }
  }
---

# CodeMCP Executor Skill

## 🎯 概述

CodeMCP Executor Skill 是一个专业的AI协同编程执行器，负责从CodeMCP服务器获取开发任务、执行功能实现、运行测试验证、提交执行结果。作为执行者角色，你负责将规划好的任务流转化为实际代码，确保功能正确实现并通过测试验证。

## ✨ 核心特性

### 🤖 智能任务获取
- **自动轮询**: 每隔5秒自动查询CodeMCP服务器获取新任务
- **任务获取**: 从服务器获取功能feature实现任务
- **优先级处理**: 按照任务优先级顺序执行
- **状态同步**: 实时同步任务状态到服务器

### 💻 代码实现与测试
- **功能实现**: 执行代码编写、模块开发、功能实现
- **测试编写**: 为功能实现编写对应的测试用例
- **测试执行**: 运行测试验证功能正确性
- **覆盖率检查**: 确保测试覆盖关键代码路径

### 🔄 自动化执行流程
- **执行环境准备**: 自动准备代码执行环境
- **依赖管理**: 检查并安装必要的依赖包
- **命令执行**: 执行开发、测试、构建等命令
- **结果验证**: 验证命令执行结果和退出码

### 🛡️ 错误处理与重试
- **失败检测**: 智能检测任务执行失败
- **自动重试**: 支持任务失败自动重试（最多3次）
- **问题诊断**: 分析失败原因并提供修复建议
- **重新执行**: 修复问题后重新执行任务

### 📊 结果提交与报告
- **结果提交**: 将执行结果提交回CodeMCP服务器
- **状态更新**: 更新任务状态（成功/失败）
- **详细报告**: 生成详细的执行报告和日志
- **进度同步**: 同步执行进度给规划器

## 🚀 快速开始

### 安装
```bash
# 1. 克隆或下载技能包
git clone <repository-url>
cd codemcp-executor-skill

# 2. 确保依赖
chmod +x scripts/*.sh

# 3. 配置CodeMCP服务器地址
export CODEMCP_SERVER_URL="http://localhost:8000"
```

### 基本使用
```bash
# 1. 启动执行器服务
./scripts/codemcp_executor.sh

# 2. 或者使用命令行模式
./scripts/codemcp_executor.sh check      # 检查环境和连接
./scripts/codemcp_executor.sh start      # 启动执行器服务
./scripts/codemcp_executor.sh fetch      # 手动获取任务
./scripts/codemcp_executor.sh status     # 查看执行器状态
```

## 📋 完整工作流

### 阶段1: 准备与连接
1. **环境检查**: 检查Python环境、依赖、网络连接
2. **服务器连接**: 连接到CodeMCP服务器
3. **身份验证**: 作为执行者角色进行身份验证
4. **初始化**: 初始化本地工作目录和配置

### 阶段2: 任务执行循环
1. **任务轮询**: 每隔5秒查询服务器获取新任务
2. **任务获取**: 获取功能feature实现任务描述
3. **任务分析**: 分析任务需求、依赖、约束条件
4. **环境准备**: 准备代码执行环境，安装必要依赖

### 阶段3: 代码实现与测试
1. **功能实现**: 根据任务要求编写代码实现功能
2. **测试编写**: 为功能实现编写对应的测试用例
3. **测试执行**: 运行测试验证功能正确性
4. **调试修复**: 如果测试失败，调试并修复问题

### 阶段4: 结果提交与清理
1. **结果验证**: 验证所有测试通过，功能完整
2. **状态更新**: 将任务状态更新为"完成"
3. **结果提交**: 提交执行结果到CodeMCP服务器
4. **环境清理**: 清理临时文件，准备下一个任务

## 🛠️ 工具脚本

### 主要脚本
- `scripts/codemcp_executor.sh` - 主执行器工作流管理器
- `scripts/fetch_task.sh` - 任务获取工具
- `scripts/execute_task.sh` - 任务执行工具
- `scripts/run_tests.sh` - 测试运行工具
- `scripts/submit_result.sh` - 结果提交工具

### 监控脚本
- `scripts/monitor_loop.sh` - 主监控循环脚本
- `scripts/check_connection.sh` - 服务器连接检查
- `scripts/report_status.sh` - 状态报告工具

### 辅助脚本
- `scripts/check_environment.sh` - 环境检查工具
- `scripts/setup_workspace.sh` - 工作空间设置工具
- `scripts/error_handler.sh` - 错误处理工具

## 📁 文件结构

```
codemcp-executor-skill/
├── SKILL.md                    # 主技能文档 (本文件)
├── README.md                   # 项目说明文档
├── LICENSE                     # 许可证文件
├── bin/                        # 可执行文件
│   └── codemcp-executor       # 主命令行工具
├── scripts/                    # 脚本文件
│   ├── codemcp_executor.sh    # 主工作流脚本
│   ├── fetch_task.sh          # 任务获取脚本
│   ├── execute_task.sh        # 任务执行脚本
│   ├── run_tests.sh           # 测试运行脚本
│   ├── submit_result.sh       # 结果提交脚本
│   ├── monitor_loop.sh        # 监控循环脚本
│   ├── check_connection.sh    # 连接检查脚本
│   ├── report_status.sh       # 状态报告脚本
│   ├── check_environment.sh   # 环境检查脚本
│   ├── setup_workspace.sh     # 工作空间设置脚本
│   └── error_handler.sh       # 错误处理脚本
├── examples/                   # 使用示例
│   ├── basic_task_execution/  # 基础任务执行示例
│   ├── feature_implementation/
│   ├── test_execution/
│   └── error_recovery/
├── docs/                       # 文档
│   ├── api_reference.md       # API接口参考
│   ├── task_format.md         # 任务格式说明
│   ├── error_handling.md      # 错误处理指南
│   └── integration_guide.md   # 集成指南
└── assets/                     # 资源文件
    ├── task_template.json     # 任务模板
    ├── result_template.json   # 结果模板
    └── config_template.json   # 配置模板
```

## 🎯 使用场景

### 场景1: 自动获取并执行任务
```bash
# 启动执行器，自动轮询并执行任务
./scripts/codemcp_executor.sh start

# 执行器会:
# 1. 每5秒检查新任务
# 2. 获取任务并执行
# 3. 运行测试验证
# 4. 提交结果
```

### 场景2: 手动获取和执行任务
```bash
# 手动获取一个任务
./scripts/fetch_task.sh --type feature

# 执行获取到的任务
./scripts/execute_task.sh --task-id TASK_001

# 运行测试
./scripts/run_tests.sh --task-id TASK_001

# 提交结果
./scripts/submit_result.sh --task-id TASK_001 --status success
```

### 场景3: 监控和故障恢复
```bash
# 监控执行器状态
./scripts/report_status.sh

# 检查服务器连接
./scripts/check_connection.sh

# 处理失败任务
./scripts/error_handler.sh --task-id TASK_001 --action retry
```

## ⚙️ 配置

### 环境变量
```bash
# CodeMCP服务器配置
export CODEMCP_SERVER_URL="http://localhost:8000"
export CODEMCP_API_KEY="your-api-key-here"

# 执行器配置
export EXECUTOR_ID="executor-001"
export EXECUTOR_NAME="AI Code Executor"
export EXECUTOR_ROLE="feature_implementation"

# 轮询配置
export POLL_INTERVAL=5               # 轮询间隔（秒）
export MAX_RETRIES=3                 # 最大重试次数
export RETRY_DELAY=10                # 重试延迟（秒）

# 执行环境配置
export WORKSPACE_DIR="/tmp/codemcp-workspace"
export LOG_LEVEL="INFO"
export ENABLE_DEBUG="false"
```

### 配置文件
创建 `~/.config/codemcp-executor/config.json`:
```json
{
  "server": {
    "url": "http://localhost:8000",
    "api_key": "your-api-key-here",
    "timeout": 30
  },
  "executor": {
    "id": "executor-001",
    "name": "AI Code Executor",
    "role": "feature_implementation",
    "capabilities": ["coding", "testing", "debugging"]
  },
  "polling": {
    "interval": 5,
    "enabled": true,
    "max_empty_polls": 10
  },
  "execution": {
    "max_retries": 3,
    "retry_delay": 10,
    "timeout": 300,
    "workspace_dir": "/tmp/codemcp-workspace"
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/codemcp-executor.log",
    "max_size_mb": 10
  },
  "notifications": {
    "enabled": false,
    "on_success": true,
    "on_failure": true,
    "on_retry": true
  }
}
```

## 🔧 集成

### 与CodeMCP Planner集成
```yaml
# CodeMCP Planner创建任务
# Executor自动获取并执行

# Planner端
./scripts/codemcp_planner.sh create-task --type feature --description "实现用户登录功能"

# Executor端 (自动运行)
# 每5秒检查新任务，发现任务后自动执行
```

### 与coding-agent协同
```bash
# Executor可以调用coding-agent执行复杂代码任务
# coding-agent负责实际编码，Executor负责任务管理和测试

# 在execute_task.sh中调用coding-agent
coding-agent --task "实现用户登录功能" --output ./implementation/
```

### 与测试框架集成
```bash
# 支持多种测试框架
# pytest (默认)
./scripts/run_tests.sh --framework pytest --path tests/

# unittest
./scripts/run_tests.sh --framework unittest --path tests/

# 自定义测试命令
./scripts/run_tests.sh --command "npm test"
```

## 🐛 故障排除

### 常见问题

#### 1. 无法连接到CodeMCP服务器
```bash
# 检查服务器状态
curl http://localhost:8000/health

# 检查网络连接
./scripts/check_connection.sh

# 更新服务器URL
export CODEMCP_SERVER_URL="http://127.0.0.1:8000"
```

#### 2. 任务执行失败
```bash
# 查看详细错误日志
tail -f /var/log/codemcp-executor.log

# 手动重试任务
./scripts/error_handler.sh --task-id TASK_001 --action retry

# 分析失败原因
./scripts/error_handler.sh --task-id TASK_001 --action analyze
```

#### 3. 测试执行失败
```bash
# 查看测试输出
./scripts/run_tests.sh --task-id TASK_001 --verbose

# 运行特定测试
pytest tests/test_feature.py::TestFeature::test_specific_function

# 调试测试问题
./scripts/execute_task.sh --task-id TASK_001 --debug
```

#### 4. 轮询不工作
```bash
# 检查轮询配置
echo $POLL_INTERVAL

# 手动测试任务获取
./scripts/fetch_task.sh --test

# 查看轮询日志
grep "polling" /var/log/codemcp-executor.log
```

### 问题报告
遇到问题时，使用标准化报告：
```bash
./scripts/error_handler.sh --report --type "连接问题" --description "无法连接到服务器"
```

## 📚 文档

### 详细文档
- `docs/api_reference.md` - CodeMCP API接口参考
- `docs/task_format.md` - 任务数据格式说明
- `docs/error_handling.md` - 详细错误处理指南
- `docs/integration_guide.md` - 与其他系统集成指南

### 示例文档
- `examples/basic_task_execution/` - 基础任务执行示例
- `examples/feature_implementation/` - 功能实现示例
- `examples/test_execution/` - 测试执行示例
- `examples/error_recovery/` - 错误恢复示例

## 🤝 贡献

### 开发指南
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送分支
5. 创建Pull Request

### 代码规范
- 使用Shell脚本编写工具
- 添加详细的注释
- 遵循现有的代码风格
- 包含测试用例

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

- 问题报告: 使用错误处理脚本或创建GitHub Issue
- 功能请求: 通过GitHub Issues提交
- 文档问题: 提交文档改进请求

## 🚀 下一步计划

### 短期目标
- [ ] 添加更多执行器角色（测试执行器、部署执行器等）
- [ ] 支持更多编程语言和框架
- [ ] 优化性能监控和报告

### 长期目标
- [ ] 分布式执行器集群支持
- [ ] 机器学习优化任务执行策略
- [ ] 提供Web管理界面

---

**版本**: 1.0.0
**最后更新**: 2026-03-17
**维护者**: OpenClaw AI Team