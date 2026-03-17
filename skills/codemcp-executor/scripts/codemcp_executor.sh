#!/bin/bash
set -euo pipefail

# CodeMCP Executor 主脚本
# 负责管理完整的执行器工作流：连接服务器、轮询任务、执行任务、提交结果

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="${HOME}/.config/codemcp-executor"
CONFIG_FILE="${CONFIG_DIR}/config.json"
LOG_FILE="${HOME}/.codemcp-executor.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo "[${timestamp}] [${level}] ${message}" >> "$LOG_FILE"
}

# 加载配置
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log "INFO" "加载配置文件: $CONFIG_FILE"
        SERVER_URL=$(jq -r '.server.url // "http://localhost:8000"' "$CONFIG_FILE")
        API_KEY=$(jq -r '.server.api_key // ""' "$CONFIG_FILE")
        POLL_INTERVAL=$(jq -r '.polling.interval // 5' "$CONFIG_FILE")
        MAX_RETRIES=$(jq -r '.execution.max_retries // 3' "$CONFIG_FILE")
        EXECUTOR_ID=$(jq -r '.executor.id // "executor-001"' "$CONFIG_FILE")
        WORKSPACE_DIR=$(jq -r '.execution.workspace_dir // "/tmp/codemcp-workspace"' "$CONFIG_FILE")
    else
        log "WARNING" "配置文件不存在，使用默认配置"
        SERVER_URL="${CODEMCP_SERVER_URL:-http://localhost:8000}"
        API_KEY="${CODEMCP_API_KEY:-}"
        POLL_INTERVAL="${POLL_INTERVAL:-5}"
        MAX_RETRIES="${MAX_RETRIES:-3}"
        EXECUTOR_ID="${EXECUTOR_ID:-executor-001}"
        WORKSPACE_DIR="${WORKSPACE_DIR:-/tmp/codemcp-workspace}"
    fi

    # 创建 workspace 目录
    mkdir -p "$WORKSPACE_DIR"
}

# 检查依赖
check_dependencies() {
    log "INFO" "检查系统依赖..."

    local missing_deps=()

    # 检查必需的命令
    for cmd in curl jq python3 git; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "缺少必需的命令: ${missing_deps[*]}"
        return 1
    fi

    # 检查Python包
    if ! python3 -c "import requests" 2>/dev/null; then
        log "WARNING" "Python requests 模块未安装，尝试安装..."
        pip install requests || {
            log "ERROR" "无法安装 requests 模块"
            return 1
        }
    fi

    log "SUCCESS" "所有依赖检查通过"
    return 0
}

# 测试服务器连接
test_connection() {
    log "INFO" "测试连接到 CodeMCP 服务器: $SERVER_URL"

    local response
    if [[ -n "$API_KEY" ]]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $API_KEY" \
            "$SERVER_URL/health" 2>/dev/null || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" \
            "$SERVER_URL/health" 2>/dev/null || echo "000")
    fi

    if [[ "$response" == "200" ]]; then
        log "SUCCESS" "服务器连接正常"
        return 0
    else
        log "ERROR" "服务器连接失败 (HTTP $response)"
        return 1
    fi
}

# 获取下一个任务
fetch_next_task() {
    log "INFO" "获取下一个任务..."

    local task_file="${WORKSPACE_DIR}/current_task.json"

    if [[ -n "$API_KEY" ]]; then
        curl -s -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            "$SERVER_URL/api/v1/tasks/next?executor_id=$EXECUTOR_ID" \
            -o "$task_file" 2>/dev/null || true
    else
        curl -s -H "Content-Type: application/json" \
            "$SERVER_URL/api/v1/tasks/next?executor_id=$EXECUTOR_ID" \
            -o "$task_file" 2>/dev/null || true
    fi

    # 检查是否获取到任务
    if [[ ! -f "$task_file" ]] || [[ ! -s "$task_file" ]]; then
        log "INFO" "没有可用的任务"
        return 1
    fi

    local task_id=$(jq -r '.id // ""' "$task_file")
    if [[ -z "$task_id" ]] || [[ "$task_id" == "null" ]]; then
        log "INFO" "没有可用的任务"
        return 1
    fi

    local task_type=$(jq -r '.type // ""' "$task_file")
    local task_title=$(jq -r '.title // ""' "$task_file")

    log "SUCCESS" "获取到任务: $task_id - $task_title ($task_type)"
    echo "$task_id"
    return 0
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

    if [[ -n "$API_KEY" ]]; then
        curl -s -X PUT \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$SERVER_URL/api/v1/tasks/$task_id/status" > /dev/null 2>&1 || true
    else
        curl -s -X PUT \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$SERVER_URL/api/v1/tasks/$task_id/status" > /dev/null 2>&1 || true
    fi
}

# 执行任务
execute_task() {
    local task_id="$1"
    local task_file="${WORKSPACE_DIR}/current_task.json"

    log "INFO" "开始执行任务: $task_id"

    # 读取任务详情
    local task_type=$(jq -r '.type // ""' "$task_file")
    local task_title=$(jq -r '.title // ""' "$task_file")
    local task_description=$(jq -r '.description // ""' "$task_file")
    local task_commands=$(jq -r '.commands // []' "$task_file")

    # 更新状态为 running
    update_task_status "$task_id" "running" "开始执行任务"

    # 创建任务工作目录
    local task_dir="${WORKSPACE_DIR}/${task_id}"
    mkdir -p "$task_dir"

    # 保存任务信息
    echo "$task_description" > "$task_dir/description.txt"
    echo "$task_commands" > "$task_dir/commands.json"

    # 执行命令
    local command_count=$(echo "$task_commands" | jq '. | length')
    for ((i=0; i<command_count; i++)); do
        local cmd=$(echo "$task_commands" | jq -r ".[$i].command // \"\"")
        local workdir=$(echo "$task_commands" | jq -r ".[$i].workdir // \"$task_dir\"")
        local timeout=$(echo "$task_commands" | jq -r ".[$i].timeout // 300")

        if [[ -n "$cmd" ]]; then
            log "INFO" "执行命令 [$((i+1))/$command_count]: $cmd"

            # 切换到工作目录
            mkdir -p "$workdir"
            pushd "$workdir" > /dev/null

            # 执行命令（带超时）
            local start_time=$(date +%s)
            local output_file="$task_dir/command_$((i+1)).log"

            if timeout "$timeout" bash -c "$cmd" > "$output_file" 2>&1; then
                local exit_code=0
                local status="成功"
            else
                local exit_code=$?
                local status="失败"
            fi

            local end_time=$(date +%s)
            local duration=$((end_time - start_time))

            log "INFO" "命令执行 $status (退出码: $exit_code, 耗时: ${duration}s)"

            # 记录命令结果
            echo "$cmd" >> "$task_dir/commands.log"
            echo "退出码: $exit_code" >> "$task_dir/commands.log"
            echo "耗时: ${duration}s" >> "$task_dir/commands.log"
            echo "---" >> "$task_dir/commands.log"

            popd > /dev/null

            # 如果命令失败，记录错误
            if [[ $exit_code -ne 0 ]]; then
                log "ERROR" "命令执行失败: $cmd"
                echo "命令失败: $cmd" >> "$task_dir/errors.log"
                cat "$output_file" >> "$task_dir/errors.log"
            fi
        fi
    done

    # 检查是否有错误
    if [[ -f "$task_dir/errors.log" ]]; then
        log "ERROR" "任务执行过程中出现错误"
        update_task_status "$task_id" "failed" "任务执行失败"
        return 1
    else
        log "SUCCESS" "任务执行完成"
        update_task_status "$task_id" "success" "任务执行成功"
        return 0
    fi
}

# 运行测试
run_tests() {
    local task_id="$1"
    local task_dir="${WORKSPACE_DIR}/${task_id}"

    log "INFO" "运行测试验证..."

    # 检查是否有测试命令
    if [[ -f "$task_dir/commands.json" ]]; then
        local test_commands=$(jq -r '.[] | select(.type == "test") | .command' "$task_dir/commands.json" 2>/dev/null || true)

        if [[ -n "$test_commands" ]]; then
            while IFS= read -r test_cmd; do
                if [[ -n "$test_cmd" ]]; then
                    log "INFO" "运行测试: $test_cmd"

                    pushd "$task_dir" > /dev/null

                    local test_output="$task_dir/test_output.log"
                    if bash -c "$test_cmd" > "$test_output" 2>&1; then
                        log "SUCCESS" "测试通过"
                    else
                        log "ERROR" "测试失败"
                        echo "测试失败: $test_cmd" >> "$task_dir/errors.log"
                        cat "$test_output" >> "$task_dir/errors.log"
                    fi

                    popd > /dev/null
                fi
            done <<< "$test_commands"
        fi
    fi

    # 如果没有测试命令，尝试运行常见的测试
    if [[ ! -f "$task_dir/commands.json" ]] || [[ -z "$test_commands" ]]; then
        log "INFO" "没有指定测试命令，尝试运行常见测试..."

        pushd "$task_dir" > /dev/null

        # 尝试运行 pytest
        if find . -name "test_*.py" -o -name "*_test.py" | grep -q .; then
            log "INFO" "发现Python测试文件，运行pytest..."
            if python -m pytest -v > "$task_dir/pytest.log" 2>&1; then
                log "SUCCESS" "pytest测试通过"
            else
                log "ERROR" "pytest测试失败"
                echo "pytest测试失败" >> "$task_dir/errors.log"
                cat "$task_dir/pytest.log" >> "$task_dir/errors.log"
            fi
        fi

        popd > /dev/null
    fi

    # 检查测试结果
    if [[ -f "$task_dir/errors.log" ]] && grep -q "测试" "$task_dir/errors.log"; then
        log "ERROR" "测试验证失败"
        return 1
    else
        log "SUCCESS" "测试验证通过"
        return 0
    fi
}

# 提交结果
submit_result() {
    local task_id="$1"
    local status="$2"
    local task_dir="${WORKSPACE_DIR}/${task_id}"

    log "INFO" "提交任务结果: $task_id -> $status"

    # 收集结果文件
    local result_file="$task_dir/result.json"
    local summary="任务执行完成"

    if [[ "$status" == "success" ]]; then
        summary="任务执行成功，所有测试通过"
    else
        summary="任务执行失败，请查看错误日志"
    fi

    # 创建结果JSON
    jq -n \
        --arg task_id "$task_id" \
        --arg status "$status" \
        --arg executor_id "$EXECUTOR_ID" \
        --arg summary "$summary" \
        --arg workspace "$task_dir" \
        '{
            task_id: $task_id,
            status: $status,
            executor_id: $executor_id,
            summary: $summary,
            workspace: $workspace,
            timestamp: now | todate
        }' > "$result_file"

    # 如果有错误日志，包含在结果中
    if [[ -f "$task_dir/errors.log" ]]; then
        local errors=$(cat "$task_dir/errors.log")
        jq --arg errors "$errors" '.errors = $errors' "$result_file" > "$result_file.tmp"
        mv "$result_file.tmp" "$result_file"
    fi

    # 上传结果到服务器
    if [[ -n "$API_KEY" ]]; then
        curl -s -X POST \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d @"$result_file" \
            "$SERVER_URL/api/v1/tasks/$task_id/result" > /dev/null 2>&1 || true
    else
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -d @"$result_file" \
            "$SERVER_URL/api/v1/tasks/$task_id/result" > /dev/null 2>&1 || true
    fi

    log "SUCCESS" "结果提交完成"
}

# 主执行循环
main_loop() {
    log "INFO" "启动 CodeMCP Executor 主循环"
    log "INFO" "执行器ID: $EXECUTOR_ID"
    log "INFO" "轮询间隔: ${POLL_INTERVAL}秒"
    log "INFO" "工作目录: $WORKSPACE_DIR"

    local empty_polls=0
    local max_empty_polls=10

    while true; do
        log "INFO" "轮询新任务..."

        # 获取下一个任务
        if task_id=$(fetch_next_task); then
            empty_polls=0

            # 执行任务
            if execute_task "$task_id"; then
                # 运行测试
                if run_tests "$task_id"; then
                    # 测试通过，提交成功结果
                    submit_result "$task_id" "success"
                else
                    # 测试失败，提交失败结果
                    submit_result "$task_id" "failed"
                fi
            else
                # 执行失败，提交失败结果
                submit_result "$task_id" "failed"
            fi

            # 清理当前任务文件
            rm -f "${WORKSPACE_DIR}/current_task.json"

        else
            # 没有任务，计数
            ((empty_polls++))
            log "INFO" "没有任务可用 (连续空轮询: $empty_polls/$max_empty_polls)"

            if [[ $empty_polls -ge $max_empty_polls ]]; then
                log "WARNING" "连续 $max_empty_polls 次没有获取到任务，暂停轮询"
                sleep 30
                empty_polls=0
            fi
        fi

        # 等待轮询间隔
        log "INFO" "等待 ${POLL_INTERVAL} 秒后继续轮询..."
        sleep "$POLL_INTERVAL"
    done
}

# 命令处理
case "${1:-}" in
    "start")
        load_config
        check_dependencies
        test_connection
        main_loop
        ;;
    "check")
        load_config
        check_dependencies
        test_connection
        log "SUCCESS" "环境检查完成，所有依赖和连接正常"
        ;;
    "fetch")
        load_config
        check_dependencies
        test_connection
        fetch_next_task
        ;;
    "test")
        load_config
        test_connection
        ;;
    "status")
        log "INFO" "CodeMCP Executor 状态"
        echo "执行器ID: ${EXECUTOR_ID:-未设置}"
        echo "服务器URL: ${SERVER_URL:-未设置}"
        echo "轮询间隔: ${POLL_INTERVAL:-5}秒"
        echo "工作目录: ${WORKSPACE_DIR:-/tmp/codemcp-workspace}"
        echo "配置文件: $CONFIG_FILE"
        echo "日志文件: $LOG_FILE"
        ;;
    "help"|"--help"|"-h"|"")
        echo "CodeMCP Executor 脚本"
        echo ""
        echo "用法: $0 <命令>"
        echo ""
        echo "命令:"
        echo "  start     启动执行器主循环"
        echo "  check     检查环境和连接"
        echo "  fetch     获取下一个任务（测试用）"
        echo "  test      测试服务器连接"
        echo "  status    查看执行器状态"
        echo "  help      显示此帮助信息"
        echo ""
        echo "环境变量:"
        echo "  CODEMCP_SERVER_URL  CodeMCP服务器地址"
        echo "  CODEMCP_API_KEY     API密钥"
        echo "  POLL_INTERVAL       轮询间隔（秒）"
        echo "  EXECUTOR_ID         执行器ID"
        echo "  WORKSPACE_DIR       工作目录"
        echo ""
        echo "配置文件: $CONFIG_FILE"
        ;;
    *)
        log "ERROR" "未知命令: $1"
        echo "使用: $0 help 查看帮助"
        exit 1
        ;;
esac