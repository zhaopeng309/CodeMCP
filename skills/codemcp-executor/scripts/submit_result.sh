#!/bin/bash
set -euo pipefail

# 结果提交脚本
# 将任务执行结果提交到CodeMCP服务器

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

# 验证结果文件
validate_result_file() {
    local result_file="$1"

    if [[ ! -f "$result_file" ]]; then
        log "ERROR" "结果文件不存在: $result_file"
        return 1
    fi

    if ! jq -e . "$result_file" > /dev/null 2>&1; then
        log "ERROR" "结果文件不是有效的JSON格式"
        return 1
    fi

    # 检查必需字段
    local task_id=$(jq -r '.task_id // ""' "$result_file")
    local status=$(jq -r '.status // ""' "$result_file")

    if [[ -z "$task_id" ]] || [[ "$task_id" == "null" ]]; then
        log "ERROR" "结果文件缺少 task_id 字段"
        return 1
    fi

    if [[ -z "$status" ]] || [[ "$status" == "null" ]]; then
        log "ERROR" "结果文件缺少 status 字段"
        return 1
    fi

    # 验证状态值
    if [[ "$status" != "success" ]] && [[ "$status" != "failed" ]] && [[ "$status" != "running" ]] && [[ "$status" != "pending" ]]; then
        log "ERROR" "无效的 status 值: $status (应为 success, failed, running, pending)"
        return 1
    fi

    log "INFO" "结果文件验证通过: task_id=$task_id, status=$status"
    return 0
}

# 准备结果数据
prepare_result_data() {
    local result_file="$1"
    local task_dir="${2:-}"

    log "INFO" "准备结果数据..."

    # 复制结果文件
    local prepared_file="/tmp/codemcp_result_prepared.json"
    cp "$result_file" "$prepared_file"

    # 添加执行器ID（如果不存在）
    local has_executor_id=$(jq 'has("executor_id")' "$prepared_file")
    if [[ "$has_executor_id" == "false" ]]; then
        jq --arg executor_id "$EXECUTOR_ID" '.executor_id = $executor_id' "$prepared_file" > "${prepared_file}.tmp"
        mv "${prepared_file}.tmp" "$prepared_file"
    fi

    # 添加时间戳（如果不存在）
    local has_timestamp=$(jq 'has("timestamp")' "$prepared_file")
    if [[ "$has_timestamp" == "false" ]]; then
        local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        jq --arg timestamp "$timestamp" '.timestamp = $timestamp' "$prepared_file" > "${prepared_file}.tmp"
        mv "${prepared_file}.tmp" "$prepared_file"
    fi

    # 如果提供了任务目录，添加详细信息
    if [[ -n "$task_dir" ]] && [[ -d "$task_dir" ]]; then
        # 添加执行日志摘要
        if [[ -f "$task_dir/errors.log" ]]; then
            local error_summary=$(head -1000 "$task_dir/errors.log")
            jq --arg error_summary "$error_summary" '.error_summary = $error_summary' "$prepared_file" > "${prepared_file}.tmp"
            mv "${prepared_file}.tmp" "$prepared_file"
        fi

        # 添加测试结果摘要
        if [[ -f "$task_dir/pytest.log" ]]; then
            local test_summary=$(tail -20 "$task_dir/pytest.log")
            jq --arg test_summary "$test_summary" '.test_summary = $test_summary' "$prepared_file" > "${prepared_file}.tmp"
            mv "${prepared_file}.tmp" "$prepared_file"
        fi

        # 添加命令执行统计
        if [[ -f "$task_dir/commands.log" ]]; then
            local command_count=$(grep -c "^命令:" "$task_dir/commands.log" 2>/dev/null || echo "0")
            jq --argjson command_count "$command_count" '.command_count = $command_count' "$prepared_file" > "${prepared_file}.tmp"
            mv "${prepared_file}.tmp" "$prepared_file"
        fi
    fi

    echo "$prepared_file"
}

# 提交结果到服务器
submit_to_server() {
    local result_file="$1"

    log "INFO" "提交结果到服务器: $SERVER_URL"

    local task_id=$(jq -r '.task_id' "$result_file")
    local status=$(jq -r '.status' "$result_file")

    log "INFO" "提交任务结果: task_id=$task_id, status=$status"

    # 构建 curl 命令
    local curl_cmd="curl -s -X POST"
    if [[ -n "$API_KEY" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $API_KEY'"
    fi

    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    curl_cmd="$curl_cmd -d @\"$result_file\""
    curl_cmd="$curl_cmd \"$SERVER_URL/api/v1/tasks/$task_id/result\""

    # 执行请求
    log "INFO" "发送HTTP请求..."
    local response_file="/tmp/codemcp_submit_response.json"
    local http_code=0

    if eval "$curl_cmd" -w "%{http_code}" -o "$response_file" 2>/dev/null | tail -1 > /tmp/http_code.txt; then
        http_code=$(cat /tmp/http_code.txt)

        if [[ $http_code -eq 200 ]] || [[ $http_code -eq 201 ]]; then
            log "SUCCESS" "结果提交成功 (HTTP $http_code)"

            # 检查响应内容
            if [[ -f "$response_file" ]] && [[ -s "$response_file" ]]; then
                if jq -e . "$response_file" > /dev/null 2>&1; then
                    local server_task_id=$(jq -r '.task_id // ""' "$response_file")
                    local server_status=$(jq -r '.status // ""' "$response_file")

                    log "INFO" "服务器响应: task_id=$server_task_id, status=$server_status"
                else
                    log "INFO" "服务器响应: $(cat "$response_file")"
                fi
            fi

            return 0
        else
            log "ERROR" "结果提交失败 (HTTP $http_code)"

            # 显示错误响应
            if [[ -f "$response_file" ]] && [[ -s "$response_file" ]]; then
                local error_msg=$(cat "$response_file")
                log "INFO" "服务器错误响应: $error_msg"
            fi

            return 1
        fi
    else
        log "ERROR" "HTTP请求失败"
        return 1
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

    if eval "$curl_cmd" > /dev/null 2>&1; then
        log "SUCCESS" "任务状态更新成功"
        return 0
    else
        log "ERROR" "任务状态更新失败"
        return 1
    fi
}

# 生成结果报告
generate_report() {
    local result_file="$1"
    local task_dir="${2:-}"
    local output_file="${3:-}"

    log "INFO" "生成结果报告..."

    local task_id=$(jq -r '.task_id // "unknown"' "$result_file")
    local status=$(jq -r '.status // "unknown"' "$result_file")
    local timestamp=$(jq -r '.timestamp // ""' "$result_file")
    local summary=$(jq -r '.summary // ""' "$result_file")

    if [[ -z "$output_file" ]]; then
        output_file="./${task_id}_report.md"
    fi

    # 生成Markdown报告
    {
        echo "# 任务执行报告"
        echo ""
        echo "## 基本信息"
        echo ""
        echo "- **任务ID**: $task_id"
        echo "- **状态**: $status"
        echo "- **执行器ID**: $EXECUTOR_ID"
        echo "- **提交时间**: ${timestamp:-$(date)}"
        echo ""
        echo "## 执行摘要"
        echo ""
        echo "$summary"
        echo ""

        # 添加错误信息
        if [[ -f "$result_file" ]]; then
            local error_summary=$(jq -r '.error_summary // ""' "$result_file")
            if [[ -n "$error_summary" ]]; then
                echo "## 错误信息"
                echo ""
                echo '```'
                echo "$error_summary"
                echo '```'
                echo ""
            fi
        fi

        # 添加测试结果
        if [[ -n "$task_dir" ]] && [[ -d "$task_dir" ]]; then
            if [[ -f "$task_dir/pytest.log" ]]; then
                echo "## 测试结果"
                echo ""
                echo '```'
                tail -50 "$task_dir/pytest.log"
                echo '```'
                echo ""
            fi

            # 列出输出文件
            echo "## 输出文件"
            echo ""
            find "$task_dir" -type f -name "*.log" -o -name "*.json" | while read -r file; do
                local filename=$(basename "$file")
                local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "?")
                echo "- $filename ($size 字节)"
            done
        fi

        echo ""
        echo "---"
        echo "*报告生成时间: $(date)*"
    } > "$output_file"

    log "SUCCESS" "结果报告已生成: $output_file"
    echo "$output_file"
}

# 主函数
main() {
    load_config

    case "${1:-}" in
        "submit")
            local result_file="${2:-}"
            local task_dir="${3:-}"

            if [[ -z "$result_file" ]]; then
                log "ERROR" "请指定结果文件"
                echo "用法: $0 submit <结果文件> [任务目录]"
                exit 1
            fi

            if [[ ! -f "$result_file" ]]; then
                log "ERROR" "结果文件不存在: $result_file"
                exit 1
            fi

            # 验证结果文件
            if ! validate_result_file "$result_file"; then
                exit 1
            fi

            # 准备结果数据
            local prepared_file=$(prepare_result_data "$result_file" "$task_dir")

            # 提交到服务器
            if submit_to_server "$prepared_file"; then
                log "SUCCESS" "结果提交完成"

                # 更新任务状态
                local task_id=$(jq -r '.task_id' "$prepared_file")
                local status=$(jq -r '.status' "$prepared_file")
                update_task_status "$task_id" "$status" "结果已提交"
            else
                log "ERROR" "结果提交失败"
                exit 1
            fi

            # 清理临时文件
            rm -f "$prepared_file"
            ;;
        "status")
            local task_id="${2:-}"
            local status="${3:-}"
            local message="${4:-}"

            if [[ -z "$task_id" ]] || [[ -z "$status" ]]; then
                log "ERROR" "请指定任务ID和状态"
                echo "用法: $0 status <任务ID> <状态> [消息]"
                echo ""
                echo "状态选项: pending, running, success, failed"
                exit 1
            fi

            update_task_status "$task_id" "$status" "$message"
            ;;
        "report")
            local result_file="${2:-}"
            local task_dir="${3:-}"
            local output_file="${4:-}"

            if [[ -z "$result_file" ]]; then
                log "ERROR" "请指定结果文件"
                echo "用法: $0 report <结果文件> [任务目录] [输出文件]"
                exit 1
            fi

            if [[ ! -f "$result_file" ]]; then
                log "ERROR" "结果文件不存在: $result_file"
                exit 1
            fi

            generate_report "$result_file" "$task_dir" "$output_file"
            ;;
        "validate")
            local result_file="${2:-}"

            if [[ -z "$result_file" ]]; then
                log "ERROR" "请指定结果文件"
                echo "用法: $0 validate <结果文件>"
                exit 1
            fi

            if [[ ! -f "$result_file" ]]; then
                log "ERROR" "结果文件不存在: $result_file"
                exit 1
            fi

            validate_result_file "$result_file"
            ;;
        "help"|"--help"|"-h"|"")
            echo "结果提交脚本"
            echo ""
            echo "用法: $0 <命令> [参数]"
            echo ""
            echo "命令:"
            echo "  submit <结果文件> [任务目录]   提交结果到服务器"
            echo "  status <任务ID> <状态> [消息]  更新任务状态"
            echo "  report <结果文件> [目录] [输出] 生成结果报告"
            echo "  validate <结果文件>            验证结果文件格式"
            echo "  help                           显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 submit result_123.json     提交结果文件"
            echo "  $0 submit result_123.json ./task_123 提交结果并包含任务目录"
            echo "  $0 status T123 success        更新任务状态为成功"
            echo "  $0 report result_123.json     生成结果报告"
            echo "  $0 validate result_123.json   验证结果文件"
            echo ""
            echo "结果文件格式示例:"
            echo '  {
                "task_id": "任务ID",
                "status": "success",
                "executor_id": "执行器ID",
                "summary": "执行摘要",
                "timestamp": "2026-03-17T10:30:00Z"
            }'
            ;;
        *)
            log "ERROR" "未知命令: $1"
            echo "使用: $0 help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"