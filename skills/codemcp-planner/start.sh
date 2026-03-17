#!/bin/bash
# start.sh - CodeMCP Planner 启动脚本

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

# 显示横幅
show_banner() {
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
║                CodeMCP Planner                          ║
║                 AI协同设计规划器                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
    echo ""
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    local missing_deps=()
    
    # 检查Git
    if ! command -v git >/dev/null 2>&1; then
        missing_deps+=("git")
    else
        log_success "Git: $(git --version | cut -d' ' -f3)"
    fi
    
    # 检查Python3
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    else
        log_success "Python3: $(python3 --version | cut -d' ' -f2)"
    fi
    
    # 检查curl
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    else
        log_success "curl: 可用"
    fi
    
    # 检查jq (可选)
    if command -v jq >/dev/null 2>&1; then
        log_success "jq: 可用"
    else
        log_warning "jq: 未安装 (JSON处理工具，建议安装)"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "缺少依赖: ${missing_deps[*]}"
        echo "请安装缺少的依赖后重试"
        exit 1
    fi
    
    log_success "所有依赖检查通过"
}

# 检查CodeMCP服务器
check_codemcp_server() {
    log_info "检查CodeMCP服务器..."
    
    local codemcp_path="${CODEMCP_PATH:-/home/designer/tools/CodeMCP}"
    
    if [ ! -d "$codemcp_path" ]; then
        log_error "CodeMCP目录不存在: $codemcp_path"
        echo "请设置正确的 CODEMCP_PATH 环境变量"
        exit 1
    fi
    
    log_success "CodeMCP目录: $codemcp_path"
    
    # 检查服务器是否运行
    if curl -s http://localhost:8000/mcp/health 2>/dev/null | grep -q "healthy"; then
        log_success "CodeMCP服务器: 运行中"
    else
        log_warning "CodeMCP服务器: 未运行"
        echo "建议启动CodeMCP服务器:"
        echo "  cd $codemcp_path && ./bin/codemcp-server"
        echo ""
    fi
}

# 设置环境
setup_environment() {
    log_info "设置工作环境..."
    
    # 获取脚本目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # 检查是否在项目目录中运行
    if [ ! -f "$SCRIPT_DIR/SKILL.md" ]; then
        log_warning "未在技能包目录中运行"
        echo "当前目录: $(pwd)"
        echo "建议在技能包目录中运行此脚本"
        echo ""
    fi
    
    # 设置执行权限
    chmod +x "$SCRIPT_DIR/scripts/"*.sh 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/bin/"* 2>/dev/null || true
    
    log_success "环境设置完成"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "📖 使用说明"
    echo "==========="
    echo ""
    echo "CodeMCP Planner 增强版提供了完整的AI协同开发管理功能:"
    echo ""
    echo "🎯 核心功能:"
    echo "  1. 项目记忆文件 - 记录项目完整历史和状态"
    echo "  2. 配置管理 - 统一保管权限密码和测试账户"
    echo "  3. 用户沟通批准 - 充分沟通后用户批准才执行"
    echo "  4. CodeMCP连接检测 - 实时监控连接状态"
    echo "  5. 流式管理 - CLI命令监控和状态汇报"
    echo ""
    echo "🚀 快速开始:"
    echo "  1. 初始化新项目: 创建记忆文件和配置"
    echo "  2. 与用户沟通: 明确需求并记录"
    echo "  3. 创建计划: 基于沟通结果创建详细计划"
    echo "  4. 用户批准: 等待用户审阅批准计划"
    echo "  5. 监控执行: 实时监控任务状态和进度"
    echo ""
    echo "🛠️  管理工具:"
    echo "  - 项目配置管理: 管理认证信息和设置"
    echo "  - 进度报告生成: 定期生成详细报告"
    echo "  - 连接状态检测: 监控CodeMCP服务器"
    echo "  - 任务状态监控: 可视化监控执行进度"
    echo ""
    echo "📁 项目文件:"
    echo "  - memory.md: 项目记忆文件，记录所有历史"
    echo "  - .codemcp-config.json: 项目配置文件"
    echo "  - *_plan.json: 项目计划文件"
    echo "  - requirements_*.md: 需求文档"
    echo "  - progress_report_*.md: 进度报告"
    echo ""
}

# 启动Planner
start_planner() {
    log_info "启动CodeMCP Planner..."
    echo ""
    
    # 进入脚本目录
    cd "$SCRIPT_DIR" || exit 1
    
    # 运行工作流管理器
    ./scripts/codemcp_planner.sh menu
}

# 主函数
main() {
    clear
    show_banner
    
    echo "版本: 2.0.0"
    echo "作者: OpenClaw AI"
    echo "许可证: MIT"
    echo ""
    
    # 检查依赖
    check_dependencies
    echo ""
    
    # 检查CodeMCP服务器
    check_codemcp_server
    echo ""
    
    # 设置环境
    setup_environment
    echo ""
    
    # 显示使用说明
    show_usage
    echo ""
    
    # 等待用户确认
    read -p "按Enter启动增强版Planner，或Ctrl+C退出..."
    echo ""
    
    # 启动Planner
    start_planner
}

# 运行主函数
main "$@"