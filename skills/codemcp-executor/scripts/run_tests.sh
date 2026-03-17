#!/bin/bash
set -euo pipefail

# 测试运行脚本
# 运行测试验证任务实现

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

# 运行 pytest 测试
run_pytest() {
    local test_path="$1"
    local task_dir="$2"
    local verbose="${3:-false}"

    log "INFO" "运行 pytest 测试: $test_path"

    local output_file="$task_dir/pytest.log"
    local coverage_file="$task_dir/coverage.xml"

    # 构建 pytest 命令
    local pytest_cmd="python -m pytest"

    if [[ "$verbose" == "true" ]]; then
        pytest_cmd="$pytest_cmd -v"
    fi

    pytest_cmd="$pytest_cmd --tb=short"

    # 添加测试路径
    if [[ -n "$test_path" ]] && [[ -e "$test_path" ]]; then
        pytest_cmd="$pytest_cmd $test_path"
    fi

    # 运行 pytest
    log "INFO" "执行命令: $pytest_cmd"

    local start_time=$(date +%s)
    if eval "$pytest_cmd" > "$output_file" 2>&1; then
        local exit_code=0
        local status="成功"
    else
        local exit_code=$?
        local status="失败"
    fi
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 检查测试结果
    if [[ $exit_code -eq 0 ]]; then
        log "SUCCESS" "pytest 测试通过 (耗时: ${duration}s)"

        # 统计测试结果
        local test_count=$(grep -c "PASSED\|FAILED\|ERROR" "$output_file" 2>/dev/null || echo "0")
        log "INFO" "测试统计: $test_count 个测试用例"

        return 0
    else
        log "ERROR" "pytest 测试失败 (退出码: $exit_code, 耗时: ${duration}s)"

        # 提取失败信息
        local error_info=$(tail -50 "$output_file")
        echo "pytest测试失败:" >> "$task_dir/errors.log"
        echo "$error_info" >> "$task_dir/errors.log"
        echo "---" >> "$task_dir/errors.log"

        return 1
    fi
}

# 运行 unittest 测试
run_unittest() {
    local test_path="$1"
    local task_dir="$2"
    local verbose="${3:-false}"

    log "INFO" "运行 unittest 测试: $test_path"

    local output_file="$task_dir/unittest.log"

    # 构建 unittest 命令
    local unittest_cmd="python -m unittest"

    if [[ "$verbose" == "true" ]]; then
        unittest_cmd="$unittest_cmd -v"
    fi

    # 添加测试路径
    if [[ -n "$test_path" ]] && [[ -e "$test_path" ]]; then
        # 如果是目录，使用 discover
        if [[ -d "$test_path" ]]; then
            unittest_cmd="$unittest_cmd discover -s $test_path -p '*test*.py'"
        # 如果是文件
        elif [[ -f "$test_path" ]]; then
            unittest_cmd="$unittest_cmd $test_path"
        fi
    else
        # 默认在当前目录发现测试
        unittest_cmd="$unittest_cmd discover -s . -p '*test*.py'"
    fi

    # 运行 unittest
    log "INFO" "执行命令: $unittest_cmd"

    local start_time=$(date +%s)
    if eval "$unittest_cmd" > "$output_file" 2>&1; then
        local exit_code=0
        local status="成功"
    else
        local exit_code=$?
        local status="失败"
    fi
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 检查测试结果
    if [[ $exit_code -eq 0 ]]; then
        log "SUCCESS" "unittest 测试通过 (耗时: ${duration}s)"
        return 0
    else
        log "ERROR" "unittest 测试失败 (退出码: $exit_code, 耗时: ${duration}s)"

        # 提取失败信息
        local error_info=$(tail -50 "$output_file")
        echo "unittest测试失败:" >> "$task_dir/errors.log"
        echo "$error_info" >> "$task_dir/errors.log"
        echo "---" >> "$task_dir/errors.log"

        return 1
    fi
}

# 运行 Node.js jest 测试
run_jest() {
    local test_path="$1"
    local task_dir="$2"
    local verbose="${3:-false}"

    log "INFO" "运行 jest 测试: $test_path"

    local output_file="$task_dir/jest.log"

    # 构建 jest 命令
    local jest_cmd="npx jest"

    if [[ "$verbose" == "true" ]]; then
        jest_cmd="$jest_cmd --verbose"
    fi

    jest_cmd="$jest_cmd --coverage"

    # 添加测试路径
    if [[ -n "$test_path" ]] && [[ -e "$test_path" ]]; then
        jest_cmd="$jest_cmd $test_path"
    fi

    # 检查 jest 是否可用
    if ! command -v npx &> /dev/null; then
        log "ERROR" "npx 不可用，无法运行 jest"
        return 1
    fi

    # 运行 jest
    log "INFO" "执行命令: $jest_cmd"

    local start_time=$(date +%s)
    if eval "$jest_cmd" > "$output_file" 2>&1; then
        local exit_code=0
        local status="成功"
    else
        local exit_code=$?
        local status="失败"
    fi
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 检查测试结果
    if [[ $exit_code -eq 0 ]]; then
        log "SUCCESS" "jest 测试通过 (耗时: ${duration}s)"
        return 0
    else
        log "ERROR" "jest 测试失败 (退出码: $exit_code, 耗时: ${duration}s)"

        # 提取失败信息
        local error_info=$(tail -50 "$output_file")
        echo "jest测试失败:" >> "$task_dir/errors.log"
        echo "$error_info" >> "$task_dir/errors.log"
        echo "---" >> "$task_dir/errors.log"

        return 1
    fi
}

# 运行自定义测试命令
run_custom_test() {
    local test_cmd="$1"
    local task_dir="$2"
    local test_name="${3:-custom_test}"

    log "INFO" "运行自定义测试: $test_name"
    log "INFO" "测试命令: $test_cmd"

    local output_file="$task_dir/${test_name}.log"

    # 运行测试命令
    local start_time=$(date +%s)
    if eval "$test_cmd" > "$output_file" 2>&1; then
        local exit_code=0
        local status="成功"
    else
        local exit_code=$?
        local status="失败"
    fi
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 检查测试结果
    if [[ $exit_code -eq 0 ]]; then
        log "SUCCESS" "自定义测试通过 (耗时: ${duration}s)"
        return 0
    else
        log "ERROR" "自定义测试失败 (退出码: $exit_code, 耗时: ${duration}s)"

        # 提取失败信息
        local error_info=$(tail -50 "$output_file")
        echo "自定义测试失败 ($test_name):" >> "$task_dir/errors.log"
        echo "命令: $test_cmd" >> "$task_dir/errors.log"
        echo "$error_info" >> "$task_dir/errors.log"
        echo "---" >> "$task_dir/errors.log"

        return 1
    fi
}

# 发现并运行测试
discover_and_run_tests() {
    local task_dir="$1"
    local framework="${2:-auto}"
    local verbose="${3:-false}"

    log "INFO" "在目录中发现并运行测试: $task_dir"
    log "INFO" "测试框架: $framework"

    # 切换到任务目录
    pushd "$task_dir" > /dev/null

    local test_found=false
    local test_passed=true

    # 自动检测测试框架
    if [[ "$framework" == "auto" ]]; then
        # 检查 pytest
        if find . -name "*test*.py" -type f | grep -q . && python -c "import pytest" 2>/dev/null; then
            log "INFO" "检测到 pytest 测试文件"
            if ! run_pytest "." "$task_dir" "$verbose"; then
                test_passed=false
            fi
            test_found=true
        # 检查 unittest
        elif find . -name "*test*.py" -type f | grep -q .; then
            log "INFO" "检测到 Python 测试文件，使用 unittest"
            if ! run_unittest "." "$task_dir" "$verbose"; then
                test_passed=false
            fi
            test_found=true
        # 检查 jest
        elif find . -name "*.test.js" -o -name "*.spec.js" | grep -q . && command -v npx &> /dev/null; then
            log "INFO" "检测到 Jest 测试文件"
            if ! run_jest "." "$task_dir" "$verbose"; then
                test_passed=false
            fi
            test_found=true
        fi
    # 指定框架
    else
        case "$framework" in
            "pytest")
                if ! run_pytest "." "$task_dir" "$verbose"; then
                    test_passed=false
                fi
                test_found=true
                ;;
            "unittest")
                if ! run_unittest "." "$task_dir" "$verbose"; then
                    test_passed=false
                fi
                test_found=true
                ;;
            "jest")
                if ! run_jest "." "$task_dir" "$verbose"; then
                    test_passed=false
                fi
                test_found=true
                ;;
            *)
                log "ERROR" "不支持的测试框架: $framework"
                test_passed=false
                ;;
        esac
    fi

    # 检查是否有测试命令文件
    if [[ -f "commands.json" ]]; then
        local test_commands=$(jq -r '.[] | select(.type == "test") | .command' "commands.json" 2>/dev/null || true)

        if [[ -n "$test_commands" ]]; then
            test_found=true
            local test_index=1

            while IFS= read -r test_cmd; do
                if [[ -n "$test_cmd" ]]; then
                    if ! run_custom_test "$test_cmd" "$task_dir" "test_command_$test_index"; then
                        test_passed=false
                    fi
                    ((test_index++))
                fi
            done <<< "$test_commands"
        fi
    fi

    # 检查是否有测试脚本
    if [[ -f "run_tests.sh" ]]; then
        log "INFO" "发现测试脚本: run_tests.sh"
        test_found=true
        if ! run_custom_test "./run_tests.sh" "$task_dir" "test_script"; then
            test_passed=false
        fi
    fi

    # 检查是否有 package.json 测试脚本
    if [[ -f "package.json" ]]; then
        local npm_test_cmd=$(jq -r '.scripts.test // ""' "package.json")
        if [[ -n "$npm_test_cmd" ]]; then
            log "INFO" "发现 npm 测试脚本: $npm_test_cmd"
            test_found=true
            if ! run_custom_test "npm test" "$task_dir" "npm_test"; then
                test_passed=false
            fi
        fi
    fi

    popd > /dev/null

    # 返回结果
    if [[ "$test_found" == false ]]; then
        log "WARNING" "未发现测试文件或测试命令"
        return 2  # 特殊退出码表示未找到测试
    elif [[ "$test_passed" == true ]]; then
        log "SUCCESS" "所有测试通过"
        return 0
    else
        log "ERROR" "有测试失败"
        return 1
    fi
}

# 主函数
main() {
    case "${1:-}" in
        "run")
            local task_dir="${2:-}"
            local framework="${3:-auto}"
            local verbose="${4:-false}"

            if [[ -z "$task_dir" ]]; then
                log "ERROR" "请指定任务目录"
                echo "用法: $0 run <任务目录> [框架] [verbose]"
                echo ""
                echo "框架选项: auto, pytest, unittest, jest"
                echo "verbose: true 或 false"
                exit 1
            fi

            if [[ ! -d "$task_dir" ]]; then
                log "ERROR" "任务目录不存在: $task_dir"
                exit 1
            fi

            discover_and_run_tests "$task_dir" "$framework" "$verbose"
            ;;
        "file")
            local test_file="${2:-}"
            local task_dir="${3:-$(pwd)}"
            local framework="${4:-auto}"
            local verbose="${5:-false}"

            if [[ -z "$test_file" ]]; then
                log "ERROR" "请指定测试文件"
                echo "用法: $0 file <测试文件> [任务目录] [框架] [verbose]"
                exit 1
            fi

            if [[ ! -e "$test_file" ]]; then
                log "ERROR" "测试文件不存在: $test_file"
                exit 1
            fi

            mkdir -p "$task_dir"

            case "$framework" in
                "pytest")
                    run_pytest "$test_file" "$task_dir" "$verbose"
                    ;;
                "unittest")
                    run_unittest "$test_file" "$task_dir" "$verbose"
                    ;;
                "jest")
                    run_jest "$test_file" "$task_dir" "$verbose"
                    ;;
                "auto")
                    # 根据文件扩展名判断
                    if [[ "$test_file" == *.py ]]; then
                        run_pytest "$test_file" "$task_dir" "$verbose"
                    elif [[ "$test_file" == *.js ]]; then
                        run_jest "$test_file" "$task_dir" "$verbose"
                    else
                        log "ERROR" "无法自动判断测试框架，请明确指定"
                        exit 1
                    fi
                    ;;
                *)
                    log "ERROR" "不支持的测试框架: $framework"
                    exit 1
                    ;;
            esac
            ;;
        "cmd")
            local test_cmd="${2:-}"
            local task_dir="${3:-$(pwd)}"
            local test_name="${4:-custom_test}"

            if [[ -z "$test_cmd" ]]; then
                log "ERROR" "请指定测试命令"
                echo "用法: $0 cmd <测试命令> [任务目录] [测试名称]"
                exit 1
            fi

            mkdir -p "$task_dir"
            run_custom_test "$test_cmd" "$task_dir" "$test_name"
            ;;
        "help"|"--help"|"-h"|"")
            echo "测试运行脚本"
            echo ""
            echo "用法: $0 <命令> [参数]"
            echo ""
            echo "命令:"
            echo "  run <任务目录> [框架] [verbose]  运行目录中的所有测试"
            echo "  file <测试文件> [目录] [框架] [verbose] 运行单个测试文件"
            echo "  cmd <测试命令> [目录] [名称]    运行自定义测试命令"
            echo "  help                            显示帮助信息"
            echo ""
            echo "框架选项:"
            echo "  auto     自动检测 (默认)"
            echo "  pytest   使用 pytest"
            echo "  unittest 使用 unittest"
            echo "  jest     使用 jest"
            echo ""
            echo "示例:"
            echo "  $0 run ./task_123             运行任务目录中的所有测试"
            echo "  $0 run ./task_123 pytest true 使用 pytest 运行测试并显示详细信息"
            echo "  $0 file tests/test_login.py   运行特定测试文件"
            echo "  $0 cmd 'npm test' ./task_123  运行 npm 测试"
            ;;
        *)
            log "ERROR" "未知命令: $1"
            echo "使用: $0 help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"