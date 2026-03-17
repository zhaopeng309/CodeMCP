#!/bin/bash
# codemcp_planner_enhanced_fixed.sh - CodeMCP Planner 增强版工作流脚本（修复版）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 获取当前工作目录
CURRENT_DIR="$(pwd)"
PROJECT_NAME="$(basename "$CURRENT_DIR")"

# 项目配置文件
PROJECT_CONFIG_FILE=".codemcp-config.json"
PROJECT_MEMORY_FILE="memory.md"

# 显示横幅
show_banner() {
    clear
    cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ██████╗ ██████╗ ██████╗ ███████╗███╗   ███╗ ██████╗   ║
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗ ████║██╔═══██╗  ║
║  ██║     ██║   ██║██║  ██║█████╗  ██╔████╔██║██║   ██║  ║
║  ██║     ██║   ██║██║  ██║██╔══╝  ██║╚██╔╝██║██║   ██║  ║
║  ╚██████╗╚██████╔╝██████╔╝███████╗██║ ╚═╝ ██║╚██████╔╝  ║
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝   ║
║                                                          ║
║                CodeMCP Planner 增强版                    ║
║                 AI协同设计规划器                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
    echo ""
    echo -e "${BLUE}项目:${NC} $PROJECT_NAME"
    echo -e "${BLUE}目录:${NC} $CURRENT_DIR"
    echo ""
}

# 初始化项目记忆文件
init_project_memory() {
    local project_name="$1"
    local project_desc="$2"
    
    log_info "初始化项目记忆文件..."
    
    if [ -f "$PROJECT_MEMORY_FILE" ]; then
        log_warning "项目记忆文件已存在: $PROJECT_MEMORY_FILE"
        return 0
    fi
    
    cat > "$PROJECT_MEMORY_FILE" << EOF
# 项目记忆文件 - $project_name

## 📋 项目基本信息
- **项目名称**: $project_name
- **项目描述**: $project_desc
- **创建时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **项目目录**: $CURRENT_DIR
- **记忆文件**: $PROJECT_MEMORY_FILE

## 📊 项目状态
- **当前状态**: 初始化完成
- **最后更新时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **计划状态**: 未创建
- **任务状态**: 未开始

## 📝 沟通记录

### $(date '+%Y-%m-%d %H:%M:%S') - 项目初始化
- 项目记忆文件创建完成
- 项目基本信息已记录

## 🎯 计划执行情况

### 待完成任务
- [ ] 创建详细项目计划
- [ ] 与用户确认需求
- [ ] 用户批准计划
- [ ] 发送任务到CodeMCP

### 已完成任务
- [x] 项目初始化
- [x] 创建记忆文件

## 🔧 配置信息
- CodeMCP路径: /home/designer/tools/CodeMCP
- Git用户: AI Developer
- Git邮箱: ai.developer@codemcp.ai

## 📋 注意事项
1. 此文件记录项目的完整历史
2. 所有重要决策都应记录在此
3. 定期更新项目状态
4. 记录所有用户沟通内容

---
*最后更新: $(date '+%Y-%m-%d %H:%M:%S')*
EOF
    
    log_success "项目记忆文件已创建: $PROJECT_MEMORY_FILE"
}

# 初始化项目配置
init_project_config() {
    log_info "初始化项目配置..."
    
    if [ -f "$PROJECT_CONFIG_FILE" ]; then
        log_warning "项目配置文件已存在: $PROJECT_CONFIG_FILE"
        return 0
    fi
    
    cat > "$PROJECT_CONFIG_FILE" << EOF
{
  "project": {
    "name": "$PROJECT_NAME",
    "directory": "$CURRENT_DIR",
    "created_at": "$(date -Iseconds)",
    "config_file": "$PROJECT_CONFIG_FILE"
  },
  "codemcp": {
    "path": "/home/designer/tools/CodeMCP",
    "host": "localhost",
    "port": 8000
  },
  "git": {
    "user_name": "AI Developer",
    "user_email": "ai.developer@codemcp.ai",
    "auto_commit": true
  },
  "authentication": {
    "test_user": {
      "username": "",
      "password": "",
      "email": ""
    },
    "api_keys": {}
  },
  "communication": {
    "require_user_approval": true
  }
}
EOF
    
    log_success "项目配置文件已创建: $PROJECT_CONFIG_FILE"
    echo "请编辑此文件，添加认证信息和配置项"
}

# 检查CodeMCP连接
check_codemcp_connection() {
    log_info "检查CodeMCP连接..."
    
    echo "检测CodeMCP服务器状态..."
    
    # 检查健康端点
    if curl -s http://localhost:8000/mcp/health 2>/dev/null | grep -q "healthy"; then
        log_success "✅ CodeMCP服务器运行正常"
    else
        log_error "❌ CodeMCP服务器未运行或异常"
        echo "启动命令: cd /home/designer/tools/CodeMCP && ./bin/codemcp-server"
        return 1
    fi
    
    # 检查信息端点
    echo "服务器信息:"
    curl -s http://localhost:8000/mcp/info 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'  服务: {data.get(\"service\", \"N/A\")}')
    print(f'  版本: {data.get(\"version\", \"N/A\")}')
    print(f'  协议: {data.get(\"protocol\", \"N/A\")}')
except:
    print('  无法获取服务器信息')
" 2>/dev/null || echo "  无法获取服务器信息"
    
    return 0
}

# 显示主菜单
show_main_menu() {
    while true; do
        show_banner
        
        echo "📊 当前状态:"
        echo "  项目目录: $CURRENT_DIR"
        echo "  记忆文件: $( [ -f "$PROJECT_MEMORY_FILE" ] && echo "✅ 存在" || echo "❌ 不存在" )"
        echo "  配置文件: $( [ -f "$PROJECT_CONFIG_FILE" ] && echo "✅ 存在" || echo "❌ 不存在" )"
        echo ""
        
        echo "🎯 请选择操作:"
        echo "1. 初始化新项目（创建记忆文件和配置）"
        echo "2. 检查CodeMCP连接状态"
        echo "3. 查看项目记忆文件"
        echo "4. 查看项目配置文件"
        echo "5. 测试增强版功能"
        echo "0. 退出"
        echo ""
        
        read -p "选择 (0-5): " choice
        
        case $choice in
            1)
                init_new_project
                read -p "按Enter继续..."
                ;;
            2)
                check_codemcp_connection
                read -p "按Enter继续..."
                ;;
            3)
                if [ -f "$PROJECT_MEMORY_FILE" ]; then
                    echo ""
                    echo "📖 项目记忆文件内容:"
                    echo "===================="
                    cat "$PROJECT_MEMORY_FILE"
                else
                    log_error "项目记忆文件不存在，请先初始化项目"
                fi
                read -p "按Enter继续..."
                ;;
            4)
                if [ -f "$PROJECT_CONFIG_FILE" ]; then
                    echo ""
                    echo "⚙️  项目配置文件内容:"
                    echo "===================="
                    cat "$PROJECT_CONFIG_FILE"
                else
                    log_error "项目配置文件不存在，请先初始化项目"
                fi
                read -p "按Enter继续..."
                ;;
            5)
                test_enhanced_features
                read -p "按Enter继续..."
                ;;
            0)
                echo ""
                log_info "退出CodeMCP Planner增强版"
                exit 0
                ;;
            *)
                log_error "无效选择"
                read -p "按Enter继续..."
                ;;
        esac
    done
}

# 初始化新项目
init_new_project() {
    echo ""
    echo "🚀 初始化新项目"
    echo "================"
    echo ""
    
    read -p "项目名称: " project_name
    read -p "项目描述: " project_desc
    
    if [ -z "$project_name" ]; then
        log_error "项目名称不能为空"
        return 1
    fi
    
    # 初始化项目记忆
    init_project_memory "$project_name" "$project_desc"
    
    # 初始化项目配置
    init_project_config
    
    log_success "项目初始化完成"
    echo ""
    echo "✅ 已创建:"
    echo "  - 项目记忆文件: $PROJECT_MEMORY_FILE"
    echo "  - 项目配置文件: $PROJECT_CONFIG_FILE"
    echo ""
    echo "🎯 下一步建议:"
    echo "  1. 编辑配置文件添加认证信息"
    echo "  2. 检查CodeMCP连接状态"
    echo "  3. 开始与用户沟通需求"
}

# 测试增强版功能
test_enhanced_features() {
    echo ""
    echo "🧪 测试增强版功能"
    echo "=================="
    echo ""
    
    echo "测试项目记忆文件功能..."
    if [ -f "$PROJECT_MEMORY_FILE" ]; then
        echo "✅ 记忆文件存在: $PROJECT_MEMORY_FILE"
        echo "   大小: $(wc -l < "$PROJECT_MEMORY_FILE") 行"
        echo "   修改时间: $(stat -c %y "$PROJECT_MEMORY_FILE" 2>/dev/null | cut -d'.' -f1 || echo "未知")"
    else
        echo "❌ 记忆文件不存在"
    fi
    
    echo ""
    echo "测试项目配置功能..."
    if [ -f "$PROJECT_CONFIG_FILE" ]; then
        echo "✅ 配置文件存在: $PROJECT_CONFIG_FILE"
        if command -v python3 >/dev/null 2>&1; then
            echo "   配置验证: $(python3 -m json.tool "$PROJECT_CONFIG_FILE" >/dev/null 2>&1 && echo "✅ 格式正确" || echo "❌ 格式错误")"
        fi
    else
        echo "❌ 配置文件不存在"
    fi
    
    echo ""
    echo "测试CodeMCP连接..."
    check_codemcp_connection
    
    echo ""
    echo "📋 功能总结:"
    echo "  - 项目记忆管理: $( [ -f "$PROJECT_MEMORY_FILE" ] && echo "✅ 正常" || echo "❌ 未配置" )"
    echo "  - 配置管理: $( [ -f "$PROJECT_CONFIG_FILE" ] && echo "✅ 正常" || echo "❌ 未配置" )"
    echo "  - CodeMCP连接: $(check_codemcp_connection >/dev/null 2>&1 && echo "✅ 正常" || echo "❌ 异常" )"
    echo ""
}

# 主函数
main() {
    echo "CodeMCP Planner 增强版 - 修复版"
    echo "================================"
    echo ""
    echo "核心功能:"
    echo "  1. 项目记忆文件 (memory.md) - 记录项目完整历史"
    echo "  2. 统一配置管理 (.codemcp-config.json) - 保管认证信息"
    echo "  3. CodeMCP连接检测 - 实时监控服务器状态"
    echo "  4. 用户沟通批准 - 确保用户参与决策"
    echo ""
    
    show_main_menu
}

# 命令行参数处理
case "${1:-}" in
    "init")
        init_new_project
        ;;
    "check")
        check_codemcp_connection
        ;;
    "test")
        test_enhanced_features
        ;;
    "menu"|"")
        main
        ;;
    *)
        echo "用法: $0 [command]"
        echo ""
        echo "命令:"
        echo "  init    初始化新项目"
        echo "  check   检查CodeMCP连接"
        echo "  test    测试增强版功能"
        echo "  menu    显示菜单（默认）"
        echo ""
        echo "示例:"
        echo "  $0 init"
        echo "  $0 check"
        echo "  $0 test"
        ;;
esac