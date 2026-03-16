#!/bin/bash
# CodeMCP 项目启动脚本
# 版本: 1.0.0
# 描述: 用于启动 CodeMCP 项目的完整环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="CodeMCP"
PROJECT_VERSION="0.1.0"
SERVER_HOST="0.0.0.0"
SERVER_PORT="8000"
DATABASE_FILE="codemcp.db"
VENV_DIR="venv"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$DEBUG" = "true" ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# 显示横幅
show_banner() {
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║  ██████╗ ██████╗ ██████╗ ███████╗███╗   ███╗ ██████╗██████╗  ║"
    echo "║ ██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗ ████║██╔════╝██╔══██╗ ║"
    echo "║ ██║     ██║   ██║██║  ██║█████╗  ██╔████╔██║██║     ██████╔╝ ║"
    echo "║ ██║     ██║   ██║██║  ██║██╔══╝  ██║╚██╔╝██║██║     ██╔═══╝  ║"
    echo "║ ╚██████╗╚██████╔╝██████╔╝███████╗██║ ╚═╝ ██║╚██████╗██║      ║"
    echo "║  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝╚═╝      ║"
    echo "║                                                          ║"
    echo "║                AI协同编排与执行服务器                    ║"
    echo "║                    版本: $PROJECT_VERSION                     ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}用法: ./start.sh [选项]${NC}"
    echo ""
    echo "选项:"
    echo "  --dev          启动开发模式（热重载）"
    echo "  --prod         启动生产模式"
    echo "  --server       只启动服务器"
    echo "  --cli          只启动CLI控制台"
    echo "  --init         只初始化环境（不启动服务）"
    echo "  --clean        清理环境（删除虚拟环境和数据库）"
    echo "  --test         运行测试"
    echo "  --docs         构建文档"
    echo "  --help         显示此帮助信息"
    echo "  --debug        启用调试模式"
    echo ""
    echo "示例:"
    echo "  ./start.sh --dev          # 启动开发环境"
    echo "  ./start.sh --prod         # 启动生产环境"
    echo "  ./start.sh --init         # 初始化环境"
    echo "  ./start.sh --server --dev # 只启动开发服务器"
    echo ""
}

# 检查Python版本
check_python_version() {
    log_info "检查Python版本..."
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请先安装Python 3.9+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        log_error "Python版本过低 ($PYTHON_VERSION)，需要Python 3.9+"
        exit 1
    fi
    
    log_info "Python版本: $PYTHON_VERSION ✓"
}

# 检查虚拟环境
check_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        if [ -d "$VENV_DIR" ]; then
            log_info "激活虚拟环境..."
            source "$VENV_DIR/bin/activate"
        else
            log_warn "未找到虚拟环境，将在当前目录创建..."
            create_venv
        fi
    else
        log_info "虚拟环境已激活: $VIRTUAL_ENV ✓"
    fi
}

# 创建虚拟环境
create_venv() {
    log_info "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    log_info "虚拟环境创建成功 ✓"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装项目
    if [ "$MODE" = "dev" ]; then
        log_info "安装开发依赖..."
        pip install -e ".[dev]"
    else
        pip install -e .
    fi
    
    log_info "依赖安装完成 ✓"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 检查alembic配置
    if [ ! -f "alembic.ini" ]; then
        log_error "未找到alembic.ini配置文件"
        exit 1
    fi
    
    # 运行数据库迁移
    if command -v alembic &> /dev/null; then
        alembic upgrade head
        log_info "数据库迁移完成 ✓"
    else
        log_error "未找到alembic命令，请确保已安装依赖"
        exit 1
    fi
    
    # 检查数据库文件
    if [ -f "$DATABASE_FILE" ]; then
        log_info "数据库文件: $DATABASE_FILE ✓"
    else
        log_warn "数据库文件未创建，可能是内存数据库或配置问题"
    fi
}

# 启动服务器
start_server() {
    log_info "启动服务器..."
    
    if [ "$MODE" = "dev" ]; then
        log_info "开发模式启动（热重载）..."
        log_info "服务器地址: http://$SERVER_HOST:$SERVER_PORT"
        log_info "API文档: http://$SERVER_HOST:$SERVER_PORT/docs"
        log_info "监控: http://$SERVER_HOST:$SERVER_PORT/redoc"
        
        uvicorn codemcp.api.server:app \
            --host "$SERVER_HOST" \
            --port "$SERVER_PORT" \
            --reload \
            --log-level info
    else
        log_info "生产模式启动..."
        log_info "服务器地址: http://$SERVER_HOST:$SERVER_PORT"
        
        uvicorn codemcp.api.server:app \
            --host "$SERVER_HOST" \
            --port "$SERVER_PORT" \
            --workers 4 \
            --log-level warning
    fi
}

# 启动CLI控制台
start_cli() {
    log_info "启动CLI控制台..."
    
    if command -v codemcp &> /dev/null; then
        log_info "输入 'help' 查看可用命令"
        log_info "输入 'exit' 退出控制台"
        echo ""
        codemcp
    else
        log_error "未找到codemcp命令，请确保已安装项目"
        exit 1
    fi
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --cov=src/codemcp --cov-report=term-missing
    else
        log_error "未找到pytest命令，请安装开发依赖: pip install -e .[dev]"
        exit 1
    fi
}

# 构建文档
build_docs() {
    log_info "构建文档..."
    
    if [ -f "scripts/build_docs.sh" ]; then
        bash scripts/build_docs.sh
    else
        log_error "未找到文档构建脚本"
        exit 1
    fi
}

# 清理环境
clean_environment() {
    log_warn "清理环境..."
    
    read -p "确定要删除虚拟环境和数据库文件吗？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 删除虚拟环境
        if [ -d "$VENV_DIR" ]; then
            log_info "删除虚拟环境: $VENV_DIR"
            rm -rf "$VENV_DIR"
        fi
        
        # 删除数据库文件
        if [ -f "$DATABASE_FILE" ]; then
            log_info "删除数据库文件: $DATABASE_FILE"
            rm -f "$DATABASE_FILE"
        fi
        
        # 删除pycache
        log_info "清理Python缓存文件..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        
        log_info "环境清理完成 ✓"
    else
        log_info "取消清理操作"
    fi
}

# 检查环境
check_environment() {
    log_info "检查环境配置..."
    
    # 检查.env文件
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        log_warn "未找到.env文件，从.env.example创建..."
        cp .env.example .env
        log_info "已创建.env文件，请根据需要修改配置"
    fi
    
    # 检查必要目录
    mkdir -p logs
    mkdir -p data
    
    log_info "环境检查完成 ✓"
}

# 主函数
main() {
    show_banner
    
    # 默认模式
    MODE="dev"
    ACTION="full"
    DEBUG="false"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                MODE="dev"
                shift
                ;;
            --prod)
                MODE="prod"
                shift
                ;;
            --server)
                ACTION="server"
                shift
                ;;
            --cli)
                ACTION="cli"
                shift
                ;;
            --init)
                ACTION="init"
                shift
                ;;
            --clean)
                ACTION="clean"
                shift
                ;;
            --test)
                ACTION="test"
                shift
                ;;
            --docs)
                ACTION="docs"
                shift
                ;;
            --debug)
                DEBUG="true"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_debug "模式: $MODE"
    log_debug "操作: $ACTION"
    
    # 执行对应操作
    case $ACTION in
        full)
            check_python_version
            check_venv
            install_dependencies
            check_environment
            init_database
            log_info "启动完整服务..."
            start_server
            ;;
        server)
            check_python_version
            check_venv
            check_environment
            start_server
            ;;
        cli)
            check_python_version
            check_venv
            check_environment
            start_cli
            ;;
        init)
            check_python_version
            check_venv
            install_dependencies
            check_environment
            init_database
            log_info "环境初始化完成 ✓"
            log_info "接下来可以运行:"
            log_info "  ./start.sh --server   # 启动服务器"
            log_info "  ./start.sh --cli      # 启动CLI控制台"
            log_info "  ./start.sh --dev      # 启动完整开发环境"
            ;;
        clean)
            clean_environment
            ;;
        test)
            check_python_version
            check_venv
            run_tests
            ;;
        docs)
            check_python_version
            check_venv
            build_docs
            ;;
    esac
}

# 捕获退出信号
trap 'log_info "脚本执行结束"; exit 0' INT TERM

# 运行主函数
main "$@"

# 脚本结束
log_info "$PROJECT_NAME 启动脚本执行完成"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"