#!/bin/bash
set -euo pipefail

# 环境检查脚本
# 检查执行器运行所需的环境依赖

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    local level="$1"
    local message="$2"

    case "$level" in
        "INFO") color="${BLUE}" ;;
        "SUCCESS") color="${GREEN}" ;;
        "WARNING") color="${YELLOW}" ;;
        "ERROR") color="${RED}" ;;
        *) color="${NC}" ;;
    esac

    echo -e "${color}[${level}]${NC} ${message}"
}

# 检查命令是否存在
check_command() {
    local cmd="$1"
    local required="${2:-true}"

    if command -v "$cmd" &> /dev/null; then
        log "SUCCESS" "✓ $cmd 已安装 ($(which "$cmd"))"
        return 0
    else
        if [[ "$required" == "true" ]]; then
            log "ERROR" "✗ $cmd 未安装 (必需)"
            return 1
        else
            log "WARNING" "⚠ $cmd 未安装 (可选)"
            return 0
        fi
    fi
}

# 检查Python包
check_python_package() {
    local package="$1"
    local required="${2:-true}"

    if python3 -c "import $package" 2>/dev/null; then
        local version=$(python3 -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
        log "SUCCESS" "✓ Python包: $package ($version)"
        return 0
    else
        if [[ "$required" == "true" ]]; then
            log "ERROR" "✗ Python包: $package 未安装 (必需)"
            return 1
        else
            log "WARNING" "⚠ Python包: $package 未安装 (可选)"
            return 0
        fi
    fi
}

# 检查Node.js包
check_node_package() {
    local package="$1"
    local required="${2:-true}"

    if command -v npm &> /dev/null; then
        if npm list -g "$package" 2>/dev/null | grep -q "$package"; then
            local version=$(npm list -g "$package" 2>/dev/null | grep "$package" | head -1 | sed 's/.*@//' || echo "unknown")
            log "SUCCESS" "✓ Node.js包: $package ($version)"
            return 0
        else
            if [[ "$required" == "true" ]]; then
                log "ERROR" "✗ Node.js包: $package 未安装 (必需)"
                return 1
            else
                log "WARNING" "⚠ Node.js包: $package 未安装 (可选)"
                return 0
            fi
        fi
    else
        if [[ "$required" == "true" ]]; then
            log "ERROR" "✗ npm 未安装，无法检查 $package"
            return 1
        else
            log "WARNING" "⚠ npm 未安装，无法检查 $package"
            return 0
        fi
    fi
}

# 检查文件权限
check_file_permission() {
    local file="$1"
    local permission="$2"  # r, w, x

    if [[ -e "$file" ]]; then
        case "$permission" in
            "r")
                if [[ -r "$file" ]]; then
                    log "SUCCESS" "✓ 文件可读: $file"
                    return 0
                else
                    log "ERROR" "✗ 文件不可读: $file"
                    return 1
                fi
                ;;
            "w")
                if [[ -w "$file" ]]; then
                    log "SUCCESS" "✓ 文件可写: $file"
                    return 0
                else
                    log "ERROR" "✗ 文件不可写: $file"
                    return 1
                fi
                ;;
            "x")
                if [[ -x "$file" ]]; then
                    log "SUCCESS" "✓ 文件可执行: $file"
                    return 0
                else
                    log "ERROR" "✗ 文件不可执行: $file"
                    return 1
                fi
                ;;
            *)
                log "ERROR" "✗ 无效的权限检查: $permission"
                return 1
                ;;
        esac
    else
        log "WARNING" "⚠ 文件不存在: $file"
        return 0
    fi
}

# 检查目录权限
check_directory_permission() {
    local dir="$1"

    if [[ -d "$dir" ]]; then
        if [[ -w "$dir" ]]; then
            log "SUCCESS" "✓ 目录可写: $dir"
            return 0
        else
            log "ERROR" "✗ 目录不可写: $dir"
            return 1
        fi
    else
        log "INFO" "创建目录: $dir"
        if mkdir -p "$dir" 2>/dev/null; then
            log "SUCCESS" "✓ 目录创建成功: $dir"
            return 0
        else
            log "ERROR" "✗ 无法创建目录: $dir"
            return 1
        fi
    fi
}

# 检查网络连接
check_network() {
    local host="${1:-google.com}"
    local port="${2:-80}"

    log "INFO" "检查网络连接: $host:$port"

    if timeout 3 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
        log "SUCCESS" "✓ 网络连接正常: $host:$port"
        return 0
    else
        log "WARNING" "⚠ 无法连接到 $host:$port"
        return 1
    fi
}

# 检查环境变量
check_env_var() {
    local var_name="$1"
    local required="${2:-false}"

    if [[ -n "${!var_name:-}" ]]; then
        log "SUCCESS" "✓ 环境变量: $var_name = ${!var_name}"
        return 0
    else
        if [[ "$required" == "true" ]]; then
            log "ERROR" "✗ 环境变量未设置: $var_name (必需)"
            return 1
        else
            log "WARNING" "⚠ 环境变量未设置: $var_name (可选)"
            return 0
        fi
    fi
}

# 检查配置文件
check_config_file() {
    local config_file="$1"
    local create_if_missing="${2:-false}"

    if [[ -f "$config_file" ]]; then
        log "SUCCESS" "✓ 配置文件存在: $config_file"

        # 检查JSON格式
        if jq -e . "$config_file" > /dev/null 2>&1; then
            log "SUCCESS" "✓ 配置文件格式有效 (JSON)"
            return 0
        else
            log "ERROR" "✗ 配置文件格式无效: $config_file"
            return 1
        fi
    else
        log "WARNING" "⚠ 配置文件不存在: $config_file"

        if [[ "$create_if_missing" == "true" ]]; then
            log "INFO" "创建默认配置文件: $config_file"

            # 创建配置目录
            local config_dir=$(dirname "$config_file")
            mkdir -p "$config_dir"

            # 创建默认配置
            cat > "$config_file" << EOF
{
  "server": {
    "url": "http://localhost:8000",
    "api_key": "",
    "timeout": 30
  },
  "executor": {
    "id": "executor-001",
    "name": "AI Code Executor",
    "role": "feature_implementation"
  },
  "polling": {
    "enabled": true,
    "interval": 5
  },
  "execution": {
    "max_retries": 3,
    "timeout": 300
  }
}
EOF

            if [[ -f "$config_file" ]]; then
                log "SUCCESS" "✓ 默认配置文件创建成功: $config_file"
                return 0
            else
                log "ERROR" "✗ 无法创建配置文件: $config_file"
                return 1
            fi
        else
            return 0
        fi
    fi
}

# 检查系统资源
check_system_resources() {
    log "INFO" "检查系统资源..."

    # 检查内存
    local free_memory=$(free -m | awk '/^Mem:/{print $4}')
    if [[ $free_memory -gt 512 ]]; then
        log "SUCCESS" "✓ 可用内存: ${free_memory}MB"
    else
        log "WARNING" "⚠ 可用内存较低: ${free_memory}MB (建议 > 512MB)"
    fi

    # 检查磁盘空间
    local free_disk=$(df -h . | awk 'NR==2 {print $4}')
    log "INFO" "可用磁盘空间: $free_disk"

    # 检查CPU核心数
    local cpu_cores=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "unknown")
    log "INFO" "CPU核心数: $cpu_cores"

    return 0
}

# 检查CodeMCP服务器连接
check_codemcp_server() {
    local server_url="${1:-http://localhost:8000}"
    local api_key="${2:-}"

    log "INFO" "检查CodeMCP服务器连接: $server_url"

    local curl_cmd="curl -s -o /dev/null -w \"%{http_code}\""
    if [[ -n "$api_key" ]]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $api_key\""
    fi

    curl_cmd="$curl_cmd \"$server_url/health\""

    local http_code
    http_code=$(eval "$curl_cmd" 2>/dev/null || echo "000")

    case "$http_code" in
        "200"|"201")
            log "SUCCESS" "✓ CodeMCP服务器连接正常 (HTTP $http_code)"
            return 0
            ;;
        "401"|"403")
            log "ERROR" "✗ CodeMCP服务器认证失败 (HTTP $http_code)"
            return 1
            ;;
        "000")
            log "ERROR" "✗ 无法连接到CodeMCP服务器 (网络错误)"
            return 1
            ;;
        *)
            log "WARNING" "⚠ CodeMCP服务器返回非预期状态码: HTTP $http_code"
            return 1
            ;;
    esac
}

# 主检查函数
main_check() {
    local all_checks_passed=true

    echo "="
    echo "CodeMCP Executor 环境检查"
    echo "="
    echo ""

    # 检查必需命令
    echo "1. 检查必需命令..."
    echo "----------------------------------------"
    check_command "bash" "true" || all_checks_passed=false
    check_command "python3" "true" || all_checks_passed=false
    check_command "pip" "true" || all_checks_passed=false
    check_command "git" "true" || all_checks_passed=false
    check_command "curl" "true" || all_checks_passed=false
    check_command "jq" "true" || all_checks_passed=false
    echo ""

    # 检查可选命令
    echo "2. 检查可选命令..."
    echo "----------------------------------------"
    check_command "node" "false"
    check_command "npm" "false"
    check_command "docker" "false"
    check_command "pytest" "false"
    echo ""

    # 检查Python包
    echo "3. 检查Python包..."
    echo "----------------------------------------"
    check_python_package "requests" "true" || all_checks_passed=false
    check_python_package "pytest" "false"
    echo ""

    # 检查目录权限
    echo "4. 检查目录权限..."
    echo "----------------------------------------"
    local workspace_dir="${WORKSPACE_DIR:-/tmp/codemcp-workspace}"
    check_directory_permission "$workspace_dir" || all_checks_passed=false
    check_directory_permission "/tmp" || all_checks_passed=false

    local config_dir="${HOME}/.config/codemcp-executor"
    check_directory_permission "$config_dir" || all_checks_passed=false
    echo ""

    # 检查配置文件
    echo "5. 检查配置文件..."
    echo "----------------------------------------"
    local config_file="${CONFIG_FILE:-$config_dir/config.json}"
    check_config_file "$config_file" "true" || all_checks_passed=false
    echo ""

    # 检查环境变量
    echo "6. 检查环境变量..."
    echo "----------------------------------------"
    check_env_var "CODEMCP_SERVER_URL" "false"
    check_env_var "CODEMCP_API_KEY" "false"
    check_env_var "EXECUTOR_ID" "false"
    echo ""

    # 检查网络连接
    echo "7. 检查网络连接..."
    echo "----------------------------------------"
    check_network "google.com" "80"

    # 检查CodeMCP服务器
    local server_url="${CODEMCP_SERVER_URL:-http://localhost:8000}"
    local api_key="${CODEMCP_API_KEY:-}"
    check_codemcp_server "$server_url" "$api_key" || {
        log "WARNING" "CodeMCP服务器连接检查失败，但环境检查继续"
    }
    echo ""

    # 检查系统资源
    echo "8. 检查系统资源..."
    echo "----------------------------------------"
    check_system_resources
    echo ""

    # 总结
    echo "="
    echo "环境检查总结"
    echo "="

    if [[ "$all_checks_passed" == "true" ]]; then
        log "SUCCESS" "✓ 所有必需检查通过！"
        echo ""
        echo "CodeMCP Executor 环境准备就绪。"
        echo "可以使用以下命令启动执行器："
        echo "  ./scripts/codemcp_executor.sh start"
        return 0
    else
        log "ERROR" "✗ 部分必需检查未通过！"
        echo ""
        echo "请修复上述错误后重试。"
        echo "常见问题解决方法："
        echo "  1. 安装缺失的命令: sudo apt-get install python3 git curl jq"
        echo "  2. 安装Python包: pip install requests"
        echo "  3. 检查目录权限: chmod 755 $workspace_dir"
        echo "  4. 设置环境变量: export CODEMCP_SERVER_URL='http://localhost:8000'"
        return 1
    fi
}

# 快速检查
quick_check() {
    echo "[快速检查]"
    echo ""

    local quick_passed=true

    # 快速检查必需命令
    for cmd in python3 git curl jq; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "✗ $cmd 未安装"
            quick_passed=false
        fi
    done

    # 检查Python包
    if ! python3 -c "import requests" 2>/dev/null; then
        echo "✗ Python requests 包未安装"
        quick_passed=false
    fi

    # 检查工作目录
    local workspace_dir="${WORKSPACE_DIR:-/tmp/codemcp-workspace}"
    if [[ ! -w "/tmp" ]]; then
        echo "✗ /tmp 目录不可写"
        quick_passed=false
    fi

    if [[ "$quick_passed" == "true" ]]; then
        echo ""
        echo "✓ 快速检查通过"
        return 0
    else
        echo ""
        echo "✗ 快速检查未通过，请运行完整检查"
        return 1
    fi
}

# 主函数
main() {
    case "${1:-}" in
        "full"|"")
            main_check
            ;;
        "quick")
            quick_check
            ;;
        "network")
            check_network "${2:-google.com}" "${3:-80}"
            ;;
        "server")
            local server_url="${2:-${CODEMCP_SERVER_URL:-http://localhost:8000}}"
            local api_key="${3:-${CODEMCP_API_KEY:-}}"
            check_codemcp_server "$server_url" "$api_key"
            ;;
        "help"|"--help"|"-h")
            echo "环境检查脚本"
            echo ""
            echo "用法: $0 <命令>"
            echo ""
            echo "命令:"
            echo "  full     完整环境检查 (默认)"
            echo "  quick    快速环境检查"
            echo "  network [主机] [端口]  检查网络连接"
            echo "  server [URL] [API密钥] 检查服务器连接"
            echo "  help     显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0         运行完整环境检查"
            echo "  $0 quick   运行快速环境检查"
            echo "  $0 network google.com 80"
            echo "  $0 server http://localhost:8000"
            ;;
        *)
            echo "未知命令: $1"
            echo "使用: $0 help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"