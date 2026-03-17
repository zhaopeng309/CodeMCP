# CodeMCP Planner Skill 安装说明

## 📋 简介

CodeMCP Planner Skill 是一个AI协同设计规划器，负责管理完整的软件开发工作流。包含项目记忆文件、配置管理、用户沟通批准等核心功能。

## 🚀 快速安装

### 1. 复制技能包
```bash
# 复制到OpenClaw技能目录
cp -r ~/mydes/CodeMCP/skills/codemcp-planner ~/tools/openclaw/skills/
```

### 2. 设置执行权限
```bash
cd ~/tools/openclaw/skills/codemcp-planner
chmod +x bin/* scripts/*.sh start.sh
```

### 3. 配置环境变量（可选）
```bash
# 设置CodeMCP路径
echo 'export CODEMCP_PATH="/home/designer/tools/CodeMCP"' >> ~/.bashrc
source ~/.bashrc
```

## 🔧 环境要求

### 必需依赖
- **Git** - 版本控制
- **Python 3.8+** - 脚本执行环境
- **curl** - HTTP请求工具

### 可选依赖
- **jq** - JSON处理工具（建议安装）
- **CodeMCP** - AI协同开发平台

## 📁 文件结构

```
codemcp-planner/
├── SKILL.md          # 主技能文档
├── README.md         # 项目说明
├── LICENSE           # MIT许可证
├── CHANGELOG.md      # 更新日志
├── INSTALL.md        # 本安装说明
├── start.sh          # 启动脚本
├── bin/              # 可执行文件
│   └── codemcp-planner
├── scripts/          # 脚本文件
│   ├── codemcp_planner.sh
│   ├── check_environment.sh
│   └── create_plan_template.sh
├── docs/             # 文档
│   └── workflow_diagram.md
├── examples/         # 示例
│   └── project_plan_template.json
└── assets/           # 资源文件
    └── plan_template_README.md
```

## 🎯 使用方法

### 启动方式
```bash
# 推荐方式：使用启动脚本
./start.sh

# 直接方式：使用工作流管理器
./scripts/codemcp_planner.sh menu
```

### 常用命令
```bash
# 初始化新项目
./scripts/codemcp_planner.sh init

# 检查CodeMCP连接
./scripts/codemcp_planner.sh check

# 环境检查
./scripts/check_environment.sh

# 创建计划模板
./scripts/create_plan_template.sh --name "项目名称"
```

## 🔍 功能验证

### 1. 检查环境
```bash
./scripts/check_environment.sh
```

### 2. 测试基本功能
```bash
./scripts/codemcp_planner.sh --help
```

### 3. 验证CodeMCP连接
```bash
./scripts/codemcp_planner.sh check
```

## 🛠️ 故障排除

### 常见问题

#### 1. 权限问题
```bash
# 设置执行权限
chmod +x bin/* scripts/*.sh start.sh
```

#### 2. 依赖缺失
```bash
# Ubuntu/Debian
sudo apt install git python3 curl jq

# macOS
brew install git python curl jq
```

#### 3. CodeMCP未运行
```bash
# 启动CodeMCP服务器
cd /path/to/CodeMCP
./bin/codemcp-server
```

#### 4. 环境变量未设置
```bash
# 设置CodeMCP路径
export CODEMCP_PATH="/path/to/CodeMCP"
```

## 📞 支持资源

### 文档参考
- **主技能文档**: `SKILL.md`
- **使用指南**: `README.md`
- **工作流程**: `docs/workflow_diagram.md`

### 问题报告
检查环境依赖后，如果仍有问题：
1. 查看错误信息
2. 检查日志输出
3. 验证配置设置

### 社区支持
- OpenClaw社区讨论
- 技能包GitHub仓库
- 文档反馈和改进建议

## 🎉 完成安装

安装完成后，您可以通过以下方式使用：

1. **启动技能**: `./start.sh`
2. **初始化项目**: 在菜单中选择"初始化新项目"
3. **创建计划**: 与用户沟通后创建详细计划
4. **监控执行**: 实时监控任务状态和进度

技能包已准备好使用，开始您的AI协同开发之旅吧！