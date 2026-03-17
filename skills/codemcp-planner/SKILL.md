---
name: codemcp-planner
description: "CodeMCP Planner Skill - AI协同设计的规划器，负责完整的开发工作流：需求分析 → 创建计划 → 发送任务流 → 监听完成 → 自动git提交。支持四层数据模型(System→Block→Feature→Test)，端到端的AI协同开发管理。"
metadata:
  {
    "openclaw": { 
      "emoji": "📋", 
      "version": "1.0.0",
      "author": "OpenClaw AI",
      "license": "MIT",
      "requires": { 
        "anyBins": ["git", "python3"],
        "anyFiles": []
      },
      "recommends": {
        "skills": ["coding-agent"]
      },
      "tags": ["codemcp", "planner", "ai-development", "project-management", "git-automation"]
    }
  }
---

# CodeMCP Planner Skill

## 🎯 概述

CodeMCP Planner Skill 是一个专业的AI协同设计规划器，负责管理完整的软件开发工作流。作为规划器角色，你负责与用户沟通确定需求，创建结构化计划，协调Executor AI agent协同工作，并管理从需求分析到自动git提交的完整生命周期。

## ✨ 核心特性

### 🏗️ 结构化计划管理
- **四层数据模型**: System → Block → Feature → Test
- **需求分析**: 将自然语言需求转换为结构化计划
- **计划模板**: 基于标准模板创建可执行的开发计划

### 🤖 AI协同工作流
- **任务流发送**: 向CodeMCP发送完整的开发任务序列
- **Executor协调**: 协调多个AI agent协同工作
- **状态监控**: 实时监控任务执行状态

### 🔄 自动化流程
- **自动git提交**: 监听feature完成事件，自动提交代码
- **进度报告**: 定期生成详细的进度报告
- **失败处理**: 智能处理任务失败，自动重新规划

### 🛠️ 开发者友好
- **简单CLI**: 使用最简单的CLI命令完成所有操作
- **问题报告**: 标准化的问题报告机制
- **透明沟通**: 保持流程透明，及时用户反馈

## 🚀 快速开始

### 安装
```bash
# 1. 克隆或下载技能包
git clone <repository-url>
cd codemcp-planner-skill

# 2. 确保依赖
chmod +x scripts/*.sh
```

### 基本使用
```bash
# 1. 运行工作流管理器
./scripts/codemcp_planner.sh

# 2. 或者使用命令行模式
./scripts/codemcp_planner.sh check      # 检查环境
./scripts/codemcp_planner.sh start      # 启动服务
./scripts/codemcp_planner.sh plan       # 创建计划
```

## 📋 完整工作流

### 阶段1: 需求分析与计划创建
1. **用户沟通**: 明确项目目标、范围和约束
2. **计划制定**: 基于四层模型创建结构化计划
3. **用户审阅**: 发送计划给用户审阅批准

### 阶段2: 任务流执行
1. **环境准备**: 启动CodeMCP服务，初始化数据库
2. **任务发送**: 发送开发任务序列到CodeMCP
3. **Executor执行**: AI agent开始执行开发任务

### 阶段3: 监控与自动化
1. **状态监控**: 实时监控任务执行状态
2. **自动提交**: 检测代码变更，自动git提交
3. **进度报告**: 定期生成进度报告

### 阶段4: 问题处理与优化
1. **失败检测**: 监控任务失败情况
2. **重新规划**: 智能重新规划失败任务
3. **流程优化**: 基于执行情况优化工作流

## 🛠️ 工具脚本

### 主要脚本
- `scripts/codemcp_planner.sh` - 主工作流管理器
- `scripts/create_plan_template.sh` - 计划模板创建工具
- `scripts/monitor_tasks.sh` - 任务监控工具
- `scripts/auto_git_commit.sh` - 自动git提交工具
- `scripts/generate_report.sh` - 进度报告生成工具

### 辅助脚本
- `scripts/check_environment.sh` - 环境检查工具
- `scripts/start_services.sh` - 服务启动工具
- `scripts/problem_report.sh` - 问题报告工具

## 📁 文件结构

```
codemcp-planner-skill/
├── SKILL.md                    # 主技能文档 (本文件)
├── README.md                   # 项目说明文档
├── LICENSE                     # 许可证文件
├── bin/                        # 可执行文件
│   └── codemcp-planner        # 主命令行工具
├── scripts/                    # 脚本文件
│   ├── codemcp_planner.sh     # 主工作流脚本
│   ├── create_plan_template.sh
│   ├── monitor_tasks.sh
│   ├── auto_git_commit.sh
│   ├── generate_report.sh
│   ├── check_environment.sh
│   ├── start_services.sh
│   └── problem_report.sh
├── examples/                   # 使用示例
│   ├── basic_workflow/
│   ├── project_plan_template.json
│   └── progress_report.md
├── docs/                       # 文档
│   ├── workflow_diagram.md
│   ├── api_reference.md
│   └── troubleshooting.md
└── assets/                     # 资源文件
    ├── plan_template.json
    └── problem_report_template.md
```

## 🎯 使用场景

### 场景1: 新项目启动
```bash
# 用户: "我需要创建一个用户管理系统"
# Planner: 与用户沟通 → 创建计划 → 启动开发工作流
./scripts/codemcp_planner.sh plan "用户管理系统" "完整的用户认证和权限管理"
```

### 场景2: 日常开发监控
```bash
# 监控正在进行的项目
./scripts/monitor_tasks.sh --project "用户管理系统"
```

### 场景3: 进度报告
```bash
# 生成进度报告
./scripts/generate_report.sh --project "用户管理系统" --output report.md
```

## ⚙️ 配置

### 环境变量
```bash
# CodeMCP路径
export CODEMCP_PATH="/home/designer/tools/CodeMCP"

# Git配置
export GIT_USER_NAME="AI Developer"
export GIT_USER_EMAIL="ai.developer@codemcp.ai"

# 监控间隔（秒）
export MONITOR_INTERVAL=30
```

### 配置文件
创建 `~/.config/codemcp-planner/config.json`:
```json
{
  "codemcp_path": "/home/designer/tools/CodeMCP",
  "git": {
    "user_name": "AI Developer",
    "user_email": "ai.developer@codemcp.ai"
  },
  "monitoring": {
    "interval": 30,
    "auto_commit": true,
    "auto_report": true
  },
  "notifications": {
    "enabled": true,
    "channel": "feishu"
  }
}
```

## 🔧 集成

### 与OpenClaw集成
```yaml
# OpenClaw配置示例
skills:
  - name: codemcp-planner
    path: /path/to/codemcp-planner-skill
    enabled: true
    triggers:
      - "创建开发计划"
      - "项目规划"
      - "AI协同开发"
      - "自动git提交"
```

### 与coding-agent协同
```bash
# coding-agent会自动从CodeMCP获取任务
# Planner负责创建计划和监控进度
./scripts/codemcp_planner.sh start  # 启动CodeMCP服务
# coding-agent自动连接并开始工作
```

## 🐛 故障排除

### 常见问题

#### 1. CodeMCP服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 使用不同端口
export CODEMCP_PORT=8080
./scripts/start_services.sh
```

#### 2. Git操作失败
```bash
# 检查Git配置
git config --list

# 设置Git用户
./scripts/auto_git_commit.sh --setup
```

#### 3. 计划导入失败
```bash
# 验证JSON格式
python3 -m json.tool < plan.json

# 使用验证工具
./scripts/create_plan_template.sh --validate plan.json
```

### 问题报告
遇到问题时，使用标准化报告：
```bash
./scripts/problem_report.sh --type "CLI命令" --description "命令执行失败"
```

## 📚 文档

### 详细文档
- `docs/workflow_diagram.md` - 工作流程图和说明
- `docs/api_reference.md` - API接口参考
- `docs/troubleshooting.md` - 详细故障排除指南

### 示例文档
- `examples/basic_workflow/` - 基础工作流示例
- `examples/advanced_workflow/` - 高级工作流示例

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

- 问题报告: 使用问题报告脚本或创建GitHub Issue
- 功能请求: 通过GitHub Issues提交
- 文档问题: 提交文档改进请求

## 🚀 下一步计划

### 短期目标
- [ ] 添加更多示例项目
- [ ] 完善测试套件
- [ ] 优化性能监控

### 长期目标
- [ ] 支持多项目并行管理
- [ ] 集成更多AI agent平台
- [ ] 提供Web管理界面

---

**版本**: 1.0.0  
**最后更新**: 2026-03-17  
**维护者**: OpenClaw AI Team