#!/bin/bash
set -euo pipefail

# 任务执行脚本
# 执行具体的任务实现

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
        WORKSPACE_DIR=$(jq -r '.execution.workspace_dir // "/tmp/codemcp-workspace"' "$CONFIG_FILE")
        MAX_RETRIES=$(jq -r '.execution.max_retries // 3' "$CONFIG_FILE")
    else
        SERVER_URL="${CODEMCP_SERVER_URL:-http://localhost:8000}"
        API_KEY="${CODEMCP_API_KEY:-}"
        EXECUTOR_ID="${EXECUTOR_ID:-executor-001}"
        WORKSPACE_DIR="${WORKSPACE_DIR:-/tmp/codemcp-workspace}"
        MAX_RETRIES="${MAX_RETRIES:-3}"
    fi
}

# 更新任务状态
update_task_status() {
    local task_id="$1"
    local status="$2"
    local message="${3:-}"

    log "INFO" "更新任务状态: $task_id -> $status"

    local payload
    if [[ -n "$message" ]]; then
        payload=$(jq -n \
            --arg status "$status" \
            --arg message "$message" \
            --arg executor_id "$EXECUTOR_ID" \
            '{status: $status, message: $message, executor_id: $executor_id}')
    else
        payload=$(jq -n \
            --arg status "$status" \
            --arg executor_id "$EXECUTOR_ID" \
            '{status: $status, executor_id: $executor_id}')
    fi

    local curl_cmd="curl -s -X PUT"
    if [[ -n "$API_KEY" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $API_KEY'"
    fi

    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    curl_cmd="$curl_cmd -d '$payload'"
    curl_cmd="$curl_cmd '$SERVER_URL/api/v1/tasks/$task_id/status'"

    eval "$curl_cmd" > /dev/null 2>&1 || true
}

# 执行任务命令
execute_commands() {
    local task_dir="$1"
    local commands_file="$2"

    log "INFO" "执行任务命令..."

    if [[ ! -f "$commands_file" ]]; then
        log "WARNING" "命令文件不存在: $commands_file"
        return 0
    fi

    local command_count=$(jq '. | length' "$commands_file")
    log "INFO" "找到 $command_count 个命令需要执行"

    for ((i=0; i<command_count; i++)); do
        local cmd=$(jq -r ".[$i].command // \"\"" "$commands_file")
        local workdir=$(jq -r ".[$i].workdir // \"$task_dir\"" "$commands_file")
        local timeout=$(jq -r ".[$i].timeout // 300" "$commands_file")
        local cmd_type=$(jq -r ".[$i].type // \"execute\"" "$commands_file")

        if [[ -z "$cmd" ]]; then
            continue
        fi

        log "INFO" "执行命令 [$((i+1))/$command_count]: $cmd"
        log "INFO" "工作目录: $workdir"
        log "INFO" "超时: ${timeout}秒"
        log "INFO" "类型: $cmd_type"

        # 创建并切换到工作目录
        mkdir -p "$workdir"
        pushd "$workdir" > /dev/null

        # 执行命令
        local start_time=$(date +%s)
        local output_file="$task_dir/command_$((i+1)).log"

        log "INFO" "开始执行命令..."
        echo "命令: $cmd" > "$output_file"
        echo "开始时间: $(date)" >> "$output_file"
        echo "工作目录: $(pwd)" >> "$output_file"
        echo "---" >> "$output_file"

        # 执行命令（带超时）
        local exit_code=0
        if timeout "$timeout" bash -c "$cmd" >> "$output_file" 2>&1; then
            exit_code=0
        else
            exit_code=$?
        fi

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo "" >> "$output_file"
        echo "---" >> "$output_file"
        echo "结束时间: $(date)" >> "$output_file"
        echo "耗时: ${duration}秒" >> "$output_file"
        echo "退出码: $exit_code" >> "$output_file"

        if [[ $exit_code -eq 0 ]]; then
            log "SUCCESS" "命令执行成功 (耗时: ${duration}s)"
        else
            log "ERROR" "命令执行失败 (退出码: $exit_code, 耗时: ${duration}s)"

            # 记录错误
            echo "命令失败: $cmd" >> "$task_dir/errors.log"
            echo "退出码: $exit_code" >> "$task_dir/errors.log"
            echo "输出:" >> "$task_dir/errors.log"
            cat "$output_file" >> "$task_dir/errors.log"
            echo "---" >> "$task_dir/errors.log"
        fi

        popd > /dev/null
    done

    # 检查是否有错误
    if [[ -f "$task_dir/errors.log" ]]; then
        log "ERROR" "命令执行过程中出现错误"
        return 1
    else
        log "SUCCESS" "所有命令执行完成"
        return 0
    fi
}

# 执行任务
execute_task() {
    local task_file="$1"
    local task_id="$2"

    log "INFO" "开始执行任务: $task_id"

    # 读取任务信息
    local task_title=$(jq -r '.title // ""' "$task_file")
    local task_type=$(jq -r '.type // ""' "$task_file")
    local task_description=$(jq -r '.description // ""' "$task_file")
    local task_commands=$(jq -r '.commands // []' "$task_file")

    log "INFO" "任务标题: $task_title"
    log "INFO" "任务类型: $task_type"
    log "INFO" "任务描述: $task_description"

    # 创建任务工作目录
    local task_dir="$WORKSPACE_DIR/$task_id"
    mkdir -p "$task_dir"

    # 保存任务信息
    cp "$task_file" "$task_dir/task.json"
    echo "$task_description" > "$task_dir/description.txt"

    # 更新状态为 running
    update_task_status "$task_id" "running" "开始执行任务"

    # 保存命令到文件
    local commands_file="$task_dir/commands.json"
    echo "$task_commands" > "$commands_file"

    # 执行重试逻辑
    local retry_count=0
    local success=false

    while [[ $retry_count -le $MAX_RETRIES ]]; do
        if [[ $retry_count -gt 0 ]]; then
            log "WARNING" "第 $retry_count 次重试执行任务"
        fi

        # 执行命令
        if execute_commands "$task_dir" "$commands_file"; then
            success=true
            break
        fi

        ((retry_count++))

        if [[ $retry_count -le $MAX_RETRIES ]]; then
            local retry_delay=10
            log "WARNING" "任务执行失败，${retry_delay}秒后重试 ($retry_count/$MAX_RETRIES)"
            sleep "$retry_delay"
        fi
    done

    # 处理执行结果
    if [[ "$success" == true ]]; then
        log "SUCCESS" "任务执行成功"
        update_task_status "$task_id" "success" "任务执行成功"

        # 生成成功报告
        local result_file="$task_dir/result.json"
        jq -n \
            --arg task_id "$task_id" \
            --arg status "success" \
            --arg executor_id "$EXECUTOR_ID" \
            --arg summary "任务执行成功，所有命令执行完成" \
            --arg workspace "$task_dir" \
            '{
                task_id: $task_id,
                status: $status,
                executor_id: $executor_id,
                summary: $summary,
                workspace: $workspace,
                timestamp: now | todate
            }' > "$result_file"

        echo "$result_file"
        return 0
    else
        log "ERROR" "任务执行失败，已达到最大重试次数"
        update_task_status "$task_id" "failed" "任务执行失败，已达到最大重试次数"

        # 生成失败报告
        local result_file="$task_dir/result.json"
        local error_summary=""
        if [[ -f "$task_dir/errors.log" ]]; then
            error_summary=$(head -20 "$task_dir/errors.log")
        fi

        jq -n \
            --arg task_id "$task_id" \
            --arg status "failed" \
            --arg executor_id "$EXECUTOR_ID" \
            --arg summary "任务执行失败: $error_summary" \
            --arg workspace "$task_dir" \
            '{
                task_id: $task_id,
                status: $status,
                executor_id: $executor_id,
                summary: $summary,
                workspace: $workspace,
                timestamp: now | todate
            }' > "$result_file"

        echo "$result_file"
        return 1
    fi
}

# 主函数
main() {
    load_config

    case "${1:-}" in
        "run")
            local task_file="${2:-}"
            local task_id="${3:-}"

            if [[ -z "$task_file" ]]; then
                log "ERROR" "请指定任务文件"
                echo "用法: $0 run <任务文件> [任务ID]"
                exit 1
            fi

            if [[ ! -f "$task_file" ]]; then
                log "ERROR" "任务文件不存在: $task_file"
                exit 1
            fi

            # 提取任务ID
            if [[ -z "$task_id" ]]; then
                task_id=$(jq -r '.id // ""' "$task_file")
                if [[ -z "$task_id" ]] || [[ "$task_id" == "null" ]]; then
                    task_id=$(basename "$task_file" .json | sed 's/^task_//')
                fi
            fi

            if [[ -z "$task_id" ]]; then
                log "ERROR" "无法确定任务ID"
                exit 1
            fi

            execute_task "$task_file" "$task_id"
            ;;
        "help"|"--help"|"-h"|"")
            echo "任务执行脚本"
            echo ""
            echo "用法: $0 <命令> [参数]"
            echo ""
            echo "命令:"
            echo "  run <任务文件> [任务ID]   执行任务"
            echo "  help                      显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 run task_123.json      执行任务文件"
            echo "  $0 run task_123.json T123 执行任务文件并指定任务ID"
            echo ""
            echo "任务文件格式:"
            echo "  {
                \"id\": \"任务ID\",
                \"title\": \"任务标题\",
                \"type\": \"任务类型\",
                \"description\": \"任务描述\",
                \"commands\": [
                    {
                        \"command\": \"执行的命令\",
                        \"workdir\": \"工作目录\",
                        \"timeout\": 300,
                        \"type\": \"execute\"
                    }
                ]
            }"
            ;;
        *)
            log "ERROR" "未知命令: $1"
            echo "使用: $0 help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"