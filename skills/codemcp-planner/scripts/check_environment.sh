#!/bin/bash
# check_environment.sh - 环境检查工具

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

# 默认配置
CODEMCP_PATH="${CODEMCP_PATH:-/home/designer/tools/CodeMCP}"

# 显示横幅
show_banner() {
    echo "========================================"
    echo "      CodeMCP Planner 环境检查工具      "
    echo "========================================"
    echo ""
}

# 检查系统信息
check_system_info() {
    log_info "检查系统信息..."
    echo "操作系统: $(uname -s)"
    echo "内核版本: $(uname -r)"
    echo "主机名: $(hostname)"
    echo "用户: $(whoami)"
    echo "工作目录: $(pwd)"
    echo ""
}

# 检查Git
check_git() {
    log_info "检查Git..."
    if command -v git >/dev/null 2>&1; then
        log_success "Git版本: $(git --version | cut -d' ' -f3)"
        
        # 检查Git配置
        echo "Git配置:"
        git config --global user.name 2>/dev/null && echo "  用户名: $(git config --global user.name)" || echo "  用户名: 未设置"
        git config --global user.email 2>/dev/null && echo "  邮箱: $(git config --global user.email)" || echo "  邮箱: 未设置"
    else
        log_error "Git未安装"
        return 1
    fi
    echo ""
}

# 检查Python
check_python() {
    log_info "检查Python..."
    if command -v python3 >/dev/null 2>&1; then
        log_success "Python版本: $(python3 --version | cut -d' ' -f2)"
        
        # 检查关键包
        echo "Python包:"
        python3 -c "import json; print('  json: 可用')" 2>/dev/null || echo "  json: 不可用"
        python3 -c "import requests; print('  requests: 可用')" 2>/dev/null || echo "  requests: 不可用"
    else
        log_warning "Python3未安装"
    fi
    echo ""
}

# 检查CodeMCP
check_codemcp() {
    log_info "检查CodeMCP..."
    
    if [ -d "$CODEMCP_PATH" ]; then
        log_success "CodeMCP目录存在: $CODEMCP_PATH"
        
        # 检查目录内容
        echo "目录内容:"
        ls -la "$CODEMCP_PATH/" | head -10
        
        # 检查bin目录
        if [ -d "$CODEMCP_PATH/bin" ]; then
            echo ""
            echo "工具检查:"
            [ -x "$CODEMCP_PATH/bin/codemcp" ] && echo "  codemcp: 可执行" || echo "  codemcp: 不可执行"
            [ -x "$CODEMCP_PATH/bin/codemcp-server" ] && echo "  codemcp-server: 可执行" || echo "  codemcp-server: 不可执行"
            [ -x "$CODEMCP_PATH/bin/codemcp-db" ] && echo "  codemcp-db: 可执行" || echo "  codemcp-db: 不可执行"
        else
            log_warning "bin目录不存在"
        fi
        
        # 检查数据库
        if [ -f "$CODEMCP_PATH/codemcp.db" ]; then
            log_success "数据库文件存在"
        else
            log_info "数据库文件不存在（可能需要初始化）"
        fi
    else
        log_error "CodeMCP目录不存在: $CODEMCP_PATH"
        return 1
    fi
    echo ""
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 检查CodeMCP服务器
    if ps aux | grep -v grep | grep -q "codemcp-server"; then
        log_success "CodeMCP服务器: 运行中"
        echo "  进程信息:"
        ps aux | grep -v grep | grep "codemcp-server" | head -1
    else
        log_info "CodeMCP服务器: 未运行"
    fi
    
    # 检查端口
    echo ""
    echo "端口检查:"
    if netstat -tln 2>/dev/null | grep -q ":8000"; then
        echo "  端口8000: 被占用"
    else
        echo "  端口8000: 可用"
    fi
    
    echo ""
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查本地连接
    if ping -c 1 127.0.0.1 >/dev/null 2>&1; then
        echo "  本地网络: 正常"
    else
        log_error "本地网络异常"
    fi
    
    # 检查外部连接（可选）
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo "  外部网络: 正常"
    else
        log_warning "外部网络不可达"
    fi
    
    echo ""
}

# 检查磁盘空间
check_disk() {
    log_info "检查磁盘空间..."
    
    echo "磁盘使用情况:"
    df -h . | tail -1
    
    echo ""
}

# 检查环境变量
check_env_vars() {
    log_info "检查环境变量..."
    
    echo "关键环境变量:"
    [ -n "$CODEMCP_PATH" ] && echo "  CODEMCP_PATH: $CODEMCP_PATH" || echo "  CODEMCP_PATH: 未设置"
    [ -n "$GIT_USER_NAME" ] && echo "  GIT_USER_NAME: $GIT_USER_NAME" || echo "  GIT_USER_NAME: 未设置"
    [ -n "$GIT_USER_EMAIL" ] && echo "  GIT_USER_EMAIL: $GIT_USER_EMAIL" || echo "  GIT_USER_EMAIL: 未设置"
    [ -n "$MONITOR_INTERVAL" ] && echo "  MONITOR_INTERVAL: $MONITOR_INTERVAL" || echo "  MONITOR_INTERVAL: 未设置"
    
    echo ""
}

# 生成检查报告
generate_report() {
    local output_file="${1:-environment_check_report_$(date '+%Y%m%d_%H%M').md}"
    
    log_info "生成检查报告: $output_file"
    
    {
        echo "# 环境检查报告"
        echo ""
        echo "**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "**检查工具**: check_environment.sh"
        echo ""
        
        echo "## 系统信息"
        echo "\`\`\`"
        uname -a
        echo "\`\`\`"
        echo ""
        
        echo "## Git信息"
        echo "\`\`\`"
        git --version 2>/dev/null || echo "Git未安装"
        echo "\`\`\`"
        echo ""
        
        echo "## Python信息"
        echo "\`\`\`"
        python3 --version 2>/dev/null || echo "Python3未安装"
        echo "\`\`\`"
        echo ""
        
        echo "## CodeMCP信息"
        echo "路径: $CODEMCP_PATH"
        echo "状态: $(ps aux | grep -v grep | grep -q "codemcp-server" && echo "运行中" || echo "未运行")"
        echo ""
        
        echo "## 磁盘空间"
        echo "\`\`\`"
        df -h . | tail -1
        echo "\`\`\`"
        echo ""
        
        echo "## 建议"
        echo "1. 确保所有必需工具已安装"
        echo "2. 配置正确的环境变量"
        echo "3. 检查网络连接"
        echo "4. 确保有足够的磁盘空间"
        
    } > "$output_file"
    
    log_success "报告已生成: $output_file"
}

# 主函数
main() {
    local check_all=false
    local check_git_only=false
    local check_codemcp_only=false
    local check_services_only=false
    local generate_report_file=""
    local verbose=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --all)
                check_all=true
                shift
                ;;
            --git)
                check_git_only=true
                shift
                ;;
            --codemcp)
                check_codemcp_only=true
                shift
                ;;
            --services)
                check_services_only=true
                shift
                ;;
            --report)
                generate_report_file="${2:-environment_check_report.md}"
                shift 2
                ;;
            --verbose|-v)
                verbose=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --all             完整检查（默认）"
                echo "  --git             仅检查Git"
                echo "  --codemcp         仅检查CodeMCP"
                echo "  --services        仅检查服务"
                echo "  --report [file]   生成检查报告"
                echo "  --verbose, -v     详细输出"
                echo "  --help, -h        显示帮助"
                exit 0
                ;;
            *)
                echo "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    show_banner
    
    # 执行检查
    if [ "$check_git_only" = true ]; then
        check_git
    elif [ "$check_codemcp_only" = true ]; then
        check_codemcp
    elif [ "$check_services_only" = true ]; then
        check_services
    else
        # 默认检查所有
        check_system_info
        check_git
        check_python
        check_codemcp
        check_services
        check_network
        check_disk
        check_env_vars
    fi
    
    # 生成报告
    if [ -n "$generate_report_file" ]; then
        generate_report "$generate_report_file"
    fi
    
    # 总结
    echo "========================================"
    echo "          环境检查完成"
    echo "========================================"
    echo ""
    echo "建议:"
    echo "1. 确保所有检查项都显示成功"
    echo "2. 修复所有错误项"
    echo "3. 警告项可能需要关注"
    echo "4. 运行 'codemcp-planner check' 进行快速检查"
    echo ""
}

# 运行主函数
main "$@"