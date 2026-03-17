---
name: codemcp-planner
description: "CodeMCP Planner Skill - AI协同设计的规划器，负责完整的开发工作流：需求分析 → 创建计划 → 发送任务流 → 监听完成 → 自动git提交。支持四层数据模型(System→Block→Feature→Test)，端到端的AI协同开发管理。包含项目记忆文件、配置管理、用户沟通批准等增强功能。"
metadata:
  {
    "openclaw": { 
      "emoji": "📋", 
      "version": "2.0.0",
      "author": "OpenClaw AI",
      "license": "MIT",
      "requires": { 
        "anyBins": ["git", "python3"],
        "anyFiles": []
      },
      "recommends": {
        "skills": ["coding-agent"]
      },
      "tags": ["codemcp", "planner", "ai-development", "project-management", "git-automation", "enhanced"]
    }
  }
---

# CodeMCP Planner Skill v2.0.0

## 🎯 概述

CodeMCP Planner Skill 是一个专业的AI协同设计规划器，负责管理完整的软件开发工作流。作为规划器角色，你负责与用户沟通确定需求，创建结构化计划，协调Executor AI agent协同工作，并管理从需求分析到自动git提交的完整生命周期。

**版本 2.0.0 增强功能**：
- ✅ **项目记忆文件** - 每个项目自动创建memory.md记录完整历史
- ✅ **统一配置管理** - .codemcp-config.json保管所有认证信息
- ✅ **用户沟通批准** - 充分沟通后用户批准才执行
- ✅ **连接状态检测** - 实时监控CodeMCP服务器状态
- ✅ **流式管理机制** - CLI命令监控和状态汇报

## ✨ 核心特性

### 🏗️ 结构化计划管理
- **四层数据模型**: System → Block → Feature → Test
- **智能需求分析**: 将自然语言需求转换为结构化计划
- **可视化计划模板**: 基于标准模板创建可执行的开发计划

### 🤖 AI协同工作流
- **智能任务分发**: 向CodeMCP发送优化的开发任务序列
- **多Agent协调**: 协调多个AI agent高效协同工作
- **实时状态监控**: 可视化监控任务执行状态和进度

### 🔄 自动化流程
- **智能Git提交**: 基于代码变更自动提交并生成有意义的提交信息
- **自动进度报告**: 定期生成详细的HTML/Markdown进度报告
- **失败智能处理**: 自动检测失败任务并重新规划

### 🆕 增强版功能
- **项目记忆系统**: 完整的项目历史记录和状态跟踪
- **配置集中管理**: 安全存储所有认证信息和设置
- **用户参与决策**: 确保用户全程参与和批准关键决策
- **连接健康监控**: 实时检测CodeMCP服务器连接状态
- **透明化沟通**: 用户始终掌握项目状态和执行进度

## 🚀 快速开始

### 安装
```bash
# 1. 确保在技能包目录
cd ~/mydes/CodeMCP/skills/codemcp-planner

# 2. 设置执行权限
chmod +x bin/* scripts/*.sh start_enhanced.sh

# 3. 检查依赖
./scripts/check_environment.sh
```

### 基本使用
```bash
# 1. 启动标准版工作流管理器
./bin/codemcp-planner

# 2. 或者使用命令行模式
./bin/codemcp-planner check      # 检查环境
./bin/codemcp-planner start      # 启动服务
./bin/codemcp-planner plan       # 创建新计划
```

### 🆕 增强版使用（推荐）
```bash
# 1. 启动增强版（包含所有新功能）
./start_enhanced.sh

# 2. 或直接运行增强版工作流
./scripts/codemcp_planner_enhanced_fixed.sh menu

# 3. 增强版命令行模式
./scripts/codemcp_planner_enhanced_fixed.sh init     # 初始化新项目
./scripts/codemcp_planner_enhanced_fixed.sh check    # 检查CodeMCP连接
./scripts/codemcp_planner_enhanced_fixed.sh test     # 测试增强版功能
```

## 📋 完整工作流

### 阶段1: 项目初始化与需求沟通
1. **项目初始化**: 创建记忆文件和配置文件
2. **用户沟通**: 充分沟通明确项目目标、范围和约束
3. **需求记录**: 所有沟通内容记录到项目记忆文件

### 阶段2: 计划创建与用户批准
1. **计划制定**: 基于四层模型创建结构化计划
2. **用户审阅**: 发送计划给用户审阅
3. **用户批准**: 用户批准后计划状态更新为已批准

### 阶段3: 环境准备与任务执行
1. **环境准备**: 启动CodeMCP服务，初始化数据库
2. **连接检测**: 验证Planner与CodeMCP的连接状态
3. **任务发送**: 发送开发任务序列到CodeMCP
4. **Executor执行**: AI agent开始执行开发任务

### 阶段4: 监控与自动化
1. **状态监控**: 实时监控任务执行状态
2. **自动提交**: 检测代码变更，自动git提交
3. **进度报告**: 定期生成进度报告
4. **用户反馈**: 实时向用户汇报执行状态

### 阶段5: 问题处理与优化
1. **失败检测**: 监控任务失败情况
2. **重新规划**: 智能重新规划失败任务
3. **流程优化**: 基于执行情况优化工作流
4. **记忆更新**: 更新项目记忆文件记录所有变更

## 🆕 增强版功能详解

### 1. 项目记忆文件系统
每个项目根目录自动创建和管理：
- **memory.md** - 记录项目完整历史、沟通记录、任务状态
- **自动更新** - 每次重要操作自动记录到记忆文件
- **状态跟踪** - 跟踪计划执行情况和未完成任务
- **用户确认** - 未完成任务需要用户确认是否继续执行

### 2. 统一配置管理
项目根目录的配置文件：
- **.codemcp-config.json** - 统一保管所有配置信息
- **权限密码管理** - 安全存储测试账户、API密钥等
- **用户只需说一次** - 配置信息永久保存，无需重复输入
- **环境隔离** - 每个项目独立配置，互不干扰

### 3. 用户沟通与批准机制
完整的工作流保障：
- **需求沟通阶段** - 与用户充分沟通，明确所有需求
- **计划创建阶段** - 基于沟通结果创建详细计划
- **用户批准阶段** - 计划必须用户批准后才执行
- **透明化流程** - 用户始终掌握项目状态和决策权

### 4. CodeMCP连接健康监控
实时监控连接状态：
- **服务器健康检查** - 检测CodeMCP服务器状态
- **WebSocket连接测试** - 验证Planner与服务器连接
- **配置验证** - 检查所有必要配置是否正确
- **自动修复建议** - 提供连接问题的解决方案

### 5. 流式管理与状态汇报
CLI命令监控和汇报：
- **实时状态监控** - 可视化监控任务执行进度
- **进度报告生成** - 定期生成详细进度报告
- **用户状态汇报** - 实时向用户汇报执行状态
- **问题自动检测** - 自动检测并报告问题

## 🛠️ 工具脚本

### 核心工作流脚本
- `scripts/codemcp_planner.sh` - 增强版工作流管理器（主脚本）
- `scripts/create_plan_template.sh` - 计划模板创建工具
- `scripts/check_environment.sh` - 环境检查工具

### 增强版专用脚本
- `start_enhanced.sh` - 增强版启动脚本（推荐，包含依赖检查和说明）
- `INSTALL_AND_VERIFY.sh` - 安装验证脚本
- `FINAL_PACKAGE_PREP.sh` - 打包准备脚本

## 📁 文件结构

```
codemcp-planner-skill/
├── SKILL.md                    # 主技能文档 (本文件)
├── README.md                   # 项目说明文档
├── LICENSE                     # MIT许可证
├── CHANGELOG.md               # 更新日志
├── INSTALL.md                # 安装说明
├── start.sh                  # 启动脚本（推荐）
├── bin/                        # 可执行文件
│   └── codemcp-planner        # 主命令行工具
├── scripts/                    # 脚本文件
│   ├── codemcp_planner.sh     # 主工作流脚本 (增强版)
│   ├── check_environment.sh   # 环境检查工具
│   └── create_plan_template.sh # 计划模板创建
├── docs/                       # 文档
│   └── workflow_diagram.md    # 工作流程图
├── examples/                   # 使用示例
│   └── project_plan_template.json # 计划模板示例
└── assets/                     # 资源文件
    └── plan_template_README.md # 计划模板说明
```

## 🎯 使用场景

### 场景1: 新项目启动（增强版）
```bash
# 1. 进入项目目录
cd /path/to/your/project

# 2. 启动增强版
~/mydes/CodeMCP/skills/codemcp-planner/start_enhanced.sh

# 3. 在菜单中选择"初始化新项目"
# 4. 与用户沟通需求
# 5. 创建并批准计划
# 6. 监控任务执行
```

### 场景2: 日常开发监控
```bash
# 使用增强版监控现有项目
cd /path/to/existing/project
~/mydes/CodeMCP/skills/codemcp-planner/scripts/codemcp_planner_enhanced_fixed.sh check
~/mydes/CodeMCP/skills/codemcp-planner/scripts/codemcp_planner_enhanced_fixed.sh monitor
```

### 场景3: 团队协作管理
```bash
# 多个AI agent协同开发
./scripts/codemcp_planner_enhanced_fixed.sh init --team "frontend,backend,database"
./scripts/codemcp_planner_enhanced_fixed.sh communicate --stakeholders "product,design,qa"
./scripts/codemcp_planner_enhanced_fixed.sh plan --parallel true
```

## ⚙️ 配置说明

### 环境变量
```bash
# 必需配置
export CODEMCP_PATH="/home/designer/tools/CodeMCP"

# 可选配置
export GIT_USER_NAME="AI Developer"
export GIT_USER_EMAIL="ai.developer@codemcp.ai"
export MONITOR_INTERVAL=30
```

### 项目配置文件 (.codemcp-config.json)
```json
{
  "project": {
    "name": "项目名称",
    "directory": "/path/to/project",
    "created_at": "2026-03-17T12:00:00+08:00"
  },
  "codemcp": {
    "path": "/home/designer/tools/CodeMCP",
    "host": "localhost",
    "port": 8000,
    "plan_template": "/home/designer/tools/CodeMCP/plan/plan_template.md"
  },
  "git": {
    "user_name": "AI Developer",
    "user_email": "ai.developer@codemcp.ai",
    "auto_commit": true,
    "commit_pattern": "feat|fix|docs|style|refactor|test|chore"
  },
  "authentication": {
    "test_user": {
      "username": "testuser",
      "password": "testpassword123",
      "email": "testuser@example.com"
    },
    "api_keys": {
      "github": "ghp_xxxxxxxxxxxx",
      "openai": "sk-xxxxxxxxxxxx"
    }
  },
  "monitoring": {
    "interval": 30,
    "alert_on_failure": true,
    "notify_user": true
  },
  "communication": {
    "require_user_approval": true,
    "approval_timeout": 3600,
    "notify_channels": []
  }
}
```

## 🔧 安装与部署

### 本地安装
```bash
# 1. 确保技能包在正确位置
cp -r ~/mydes/CodeMCP/skills/codemcp-planner /path/to/your/skills/

# 2. 设置执行权限
chmod +x /path/to/your/skills/codemcp-planner/bin/*
chmod +x /path/to/your/skills/codemcp-planner/scripts/*.sh
chmod +x /path/to/your/skills/codemcp-planner/start_enhanced.sh

# 3. 配置环境变量
echo 'export CODEMCP_PATH="/home/designer/tools/CodeMCP"' >> ~/.bashrc
source ~/.bashrc

# 4. 测试安装
/path/to/your/skills/codemcp-planner/scripts/check_environment.sh
```

### OpenClaw集成
```yaml
# OpenClaw配置文件示例
skills:
  - name: codemcp-planner
    path: /path/to/your/skills/codemcp-planner
    enabled: true
    version: "2.0.0"
    triggers:
      - "创建开发计划"
      - "项目规划"
      - "AI协同开发"
      - "CodeMCP计划"
      - "任务分解"
      - "自动git提交"
      - "任务流管理"
    metadata:
      emoji: "📋"
      category: "development"
      priority: 10
```

## 📊 质量保证

### 代码质量
- 遵循Shell脚本最佳实践
- 完整的错误处理和日志记录
- 模块化设计和代码复用
- 详细的代码注释和文档

### 测试覆盖
- 环境检查测试
- 功能集成测试
- 错误处理测试
- 性能基准测试

### 用户体验
- 直观的命令行界面
- 清晰的错误信息和帮助文档
- 交互式工作流引导
- 实时进度反馈

## 🚀 发布信息

### 版本 2.0.0 (增强版)
- **发布日期**: 2026-03-17
- **状态**: 生产就绪
- **许可证**: MIT
- **依赖**: CodeMCP, Git, Python3, curl

### 新功能
1. ✅ 项目记忆文件系统
2. ✅ 统一配置管理
3. ✅ 用户沟通批准机制
4. ✅ CodeMCP连接健康监控
5. ✅ 流式管理与状态汇报

### 兼容性
- **OpenClaw**: 完全兼容
- **CodeMCP**: 需要CodeMCP 1.0+
- **操作系统**: Linux, macOS, WSL2
- **Shell**: Bash 4.0+

## 🤝 贡献指南

### 报告问题
1. 使用问题报告脚本：`./scripts/problem_report.sh`
2. 或创建GitHub Issue
3. 包含详细的重现步骤和环境信息

### 提交代码
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 开发规范
- 遵循现有的代码风格
- 添加详细的注释和文档
- 包含测试用例
- 更新相关文档

## 📞 支持与联系

- **文档**: 查看README.md和docs/目录
- **问题**: 使用问题报告工具或查看troubleshooting.md
- **讨论**: OpenClaw社区
- **贡献**: 欢迎Pull Request和功能建议

## 🎉 总结

CodeMCP Planner Skill v2.0.0 增强版提供了完整的AI协同开发管理解决方案：

1. **✅ 项目记忆系统** - 完整记录项目历史和状态
2. **✅ 配置集中管理** - 安全保管所有认证信息
3. **✅ 用户参与决策** - 确保透明化和用户批准
4. **✅ 连接健康监控** - 实时检测服务器状态
5. **✅ 流式状态汇报** - CLI命令监控和进度报告

技能包已按照标准SKILL格式编写，包含所有必要的文档、示例和工具，可以直接发布和使用！

**技能位置**: `