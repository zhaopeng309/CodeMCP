#!/bin/bash
set -euo pipefail

# 任务获取脚本
# 从CodeMCP服务器获取任务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="${HOME}/.config/codemcp-executor"
CONFIG_FILE="${CONFIG_DIR}/config.json"

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
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO") color="${BLUE}" ;;
        "SUCCESS") color="${GREEN}" ;;
        "WARNING") color="${YELLOW}" ;;
        "ERROR") color="${RED}" ;;
        *) color="${NC}" ;;
    esac

    echo -e "${color}[${timestamp}] [${level}] ${message}${NC}"
}

# 加载配置
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        SERVER_URL=$(jq -r '.server.url // "http://localhost:8000"' "$CONFIG_FILE")
        API_KEY=$(jq -r '.server.api_key // ""' "$CONFIG_FILE")
        EXECUTOR_ID=$(jq -r '.executor.id // "executor-001"' "$CONFIG_FILE")
    else
        SERVER_URL="${CODEMCP_SERVER_URL:-http://localhost:8000}"
        API_KEY="${CODEMCP_API_KEY:-}"
        EXECUTOR_ID="${EXECUTOR_ID:-executor-001}"
    fi
}

# 获取任务
fetch_task() {
    local task_type="${1:-}"
    local priority="${2:-}"

    log "INFO" "从服务器获取任务..."
    log "INFO" "服务器: $SERVER_URL"
    log "INFO" "执行器ID: $EXECUTOR_ID"

    # 构建查询参数
    local query="executor_id=$EXECUTOR_ID"
    if [[ -n "$task_type" ]]; then
        query="${query}&type=$task_type"
    fi
    if [[ -n "$priority" ]]; then
        query="${query}&priority=$priority"
    fi

    # 发送请求
    local response_file="/tmp/codemcp_task_response.json"
    local curl_cmd="curl -s"

    if [[ -n "$API_KEY" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $API_KEY'"
    fi

    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    curl_cmd="$curl_cmd '$SERVER_URL/api/v1/tasks/next?$query'"
    curl_cmd="$curl_cmd -o $response_file"

    eval "$curl_cmd"

    # 检查响应
    if [[ ! -f "$response_file" ]] || [[ ! -s "$response_file" ]]; then
        log "ERROR" "获取任务失败或服务器无响应"
        return 1
    fi

    # 检查响应内容
    if ! jq -e . "$response_file" > /dev/null 2>&1; then
        log "ERROR" "服务器返回无效的JSON响应"
        cat "$response_file"
        return 1
    fi

    # 检查是否真的获取到任务
    local task_id=$(jq -r '.id // ""' "$response_file")
    if [[ -z "$task_id" ]] || [[ "$task_id" == "null" ]]; then
        log "INFO" "没有可用的任务"
        return 1
    fi

    # 显示任务信息
    local task_title=$(jq -r '.title // ""' "$response_file")
    local task_type=$(jq -r '.type // ""' "$response_file")
    local task_priority=$(jq -r '.priority // ""' "$response_file")
    local task_description=$(jq -r '.description // ""' "$response_file")

    log "SUCCESS" "获取到任务!"
    echo ""
    echo "任务ID:   $task_id"
    echo "标题:     $task_title"
    echo "类型:     $task_type"
    echo "优先级:   $task_priority"
    echo "描述:     $task_description"
    echo ""

    # 保存任务文件
    local task_file="./task_${task_id}.json"
    cp "$response_file" "$task_file"
    log "INFO" "任务已保存到: $task_file"

    # 输出任务文件路径
    echo "$task_file"
    return 0
}

# 列出可用任务
list_tasks() {
    log "INFO" "获取可用任务列表..."

    local curl_cmd="curl -s"
    if [[ -n "$API_KEY" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $API_KEY'"
    fi

    curl_cmd="$curl_cmd '$SERVER_URL/api/v1/tasks?status=pending&limit=10'"
    local response=$(eval "$curl_cmd")

    if echo "$response" | jq -e . > /dev/null 2>&1; then
        local count=$(echo "$response" | jq '.tasks | length')
        log "INFO" "找到 $count 个待处理任务"

        if [[ $count -gt 0 ]]; then
            echo "$response" | jq -r '.tasks[] | "\(.id) | \(.title) | \(.type) | \(.priority) | \(.created_at)"' | \
                while IFS='|' read -r id title type priority created_at; do
                    printf "%-20s %-30s %-15s %-10s %s\n" \
                        "$id" "$title" "$type" "$priority" "$created_at"
                done
        fi
    else
        log "ERROR" "获取任务列表失败"
    fi
}

# 主函数
main() {
    load_config

    case "${1:-}" in
        "list")
            list_tasks
            ;;
        "get"|"fetch")
            local task_type="${2:-}"
            local priority="${3:-}"
            fetch_task "$task_type" "$priority"
            ;;
        "help"|"--help"|"-h"|"")
            echo "任务获取脚本"
            echo ""
            echo "用法: $0 <命令> [参数]"
            echo ""
            echo "命令:"
            echo "  get|fetch [type] [priority]  获取任务（可指定类型和优先级）"
            echo "  list                         列出可用任务"
            echo "  help                         显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 fetch                     获取任意任务"
            echo "  $0 fetch feature high        获取高优先级功能任务"
            echo "  $0 list                      列出所有待处理任务"
            ;;
        *)
            log "ERROR" "未知命令: $1"
            echo "使用: $0 help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"