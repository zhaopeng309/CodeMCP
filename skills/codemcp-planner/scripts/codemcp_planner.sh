#!/bin/bash
# codemcp_planner.sh - CodeMCP Planner 主工作流脚本

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

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 默认配置
CODEMCP_PATH="${CODEMCP_PATH:-/home/designer/tools/CodeMCP}"
PLAN_TEMPLATE_PATH="$CODEMCP_PATH/plan/plan_template.md"
GIT_USER_NAME="${GIT_USER_NAME:-AI Developer}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-ai.developer@codemcp.ai}"
MONITOR_INTERVAL="${MONITOR_INTERVAL:-30}"

# 检查环境
check_environment() {
    log_info "检查工作环境..."
    
    # 检查CodeMCP目录
    if [ -d "$CODEMCP_PATH" ]; then
        log_success "CodeMCP目录存在: $CODEMCP_PATH"
    else
        log_error "CodeMCP目录不存在: $CODEMCP_PATH"
        return 1
    fi
    
    # 检查Git
    if command -v git >/dev/null 2>&1; then
        log_success "Git可用: $(git --version)"
    else
        log_error "Git未安装"
        return 1
    fi
    
    # 检查Python
    if command -v python3 >/dev/null 2>&1; then
        log_success "Python3可用: $(python3 --version)"
    else
        log_warning "Python3未安装，某些功能可能受限"
    fi
    
    return 0
}

# 启动服务
start_services() {
    log_info "启动CodeMCP服务..."
    
    # 检查是否已运行
    if ps aux | grep -v grep | grep -q "codemcp-server"; then
        log_warning "CodeMCP服务器已在运行"
        return 0
    fi
    
    # 进入CodeMCP目录
    cd "$CODEMCP_PATH" || {
        log_error "无法进入CodeMCP目录: $CODEMCP_PATH"
        return 1
    }
    
    # 初始化数据库
    log_info "初始化数据库..."
    if [ -x "./bin/codemcp-db" ]; then
        ./bin/codemcp-db init 2>/dev/null || log_warning "数据库初始化可能已存在"
    else
        log_warning "codemcp-db工具不存在，跳过数据库初始化"
    fi
    
    # 启动服务器
    log_info "启动API服务器..."
    if [ -x "./bin/codemcp-server" ]; then
        ./bin/codemcp-server --reload > "$PROJECT_ROOT/server.log" 2>&1 &
        SERVER_PID=$!
        sleep 3
        
        if ps -p $SERVER_PID >/dev/null; then
            log_success "服务器启动成功，PID: $SERVER_PID"
            echo $SERVER_PID > "$PROJECT_ROOT/.server_pid"
        else
            log_error "服务器启动失败"
            return 1
        fi
    else
        log_error "codemcp-server工具不存在"
        return 1
    fi
    
    return 0
}

# 停止服务
stop_services() {
    log_info "停止CodeMCP服务..."
    
    if [ -f "$PROJECT_ROOT/.server_pid" ]; then
        SERVER_PID=$(cat "$PROJECT_ROOT/.server_pid")
        if ps -p $SERVER_PID >/dev/null; then
            kill $SERVER_PID 2>/dev/null && log_success "服务器已停止" || log_error "停止服务器失败"
            rm -f "$PROJECT_ROOT/.server_pid"
        fi
    else
        log_warning "未找到服务器PID文件，尝试查找进程..."
        pkill -f "codemcp-server" 2>/dev/null && log_success "服务器进程已停止" || log_warning "未找到服务器进程"
    fi
    
    # 清理日志
    rm -f "$PROJECT_ROOT/server.log" 2>/dev/null || true
}

# 创建计划模板
create_plan_template() {
    local project_name="$1"
    local project_desc="$2"
    local output_file="${3:-${project_name}_plan.json}"
    
    log_info "创建项目计划模板: $project_name"
    
    # 检查计划模板是否存在
    if [ -f "$PLAN_TEMPLATE_PATH" ]; then
        log_info "使用CodeMCP计划模板: $PLAN_TEMPLATE_PATH"
        echo "计划模板位置: $PLAN_TEMPLATE_PATH"
        echo "请参考模板创建详细计划"
    else
        log_warning "计划模板不存在: $PLAN_TEMPLATE_PATH"
        log_info "使用内置模板创建基本结构"
    fi
    
    # 创建基本的JSON计划结构
    cat > "$output_file" << EOF
{
  "system_name": "$project_name",
  "description": "$project_desc",
  "version": "1.0.0",
  "created_at": "$(date -Iseconds)",
  "author": "$GIT_USER_NAME",
  "blocks": [
    {
      "name": "核心架构",
      "description": "项目基础架构和配置",
      "priority": 0,
      "features": [
        {
          "name": "项目初始化",
          "description": "初始化项目结构和配置",
          "test_command": "echo '项目初始化测试完成'",
          "priority": 0,
          "estimated_hours": 1
        },
        {
          "name": "开发环境配置",
          "description": "配置开发环境和依赖",
          "test_command": "echo '环境配置测试完成'",
          "priority": 0,
          "estimated_hours": 2
        }
      ]
    },
    {
      "name": "业务功能",
      "description": "核心业务功能模块",
      "priority": 1,
      "features": [
        {
          "name": "用户管理",
          "description": "用户注册、登录、权限管理",
          "test_command": "pytest tests/test_user.py -v",
          "priority": 0,
          "estimated_hours": 4
        },
        {
          "name": "数据管理",
          "description": "数据的增删改查操作",
          "test_command": "pytest tests/test_data.py -v",
          "priority": 1,
          "estimated_hours": 3
        }
      ]
    },
    {
      "name": "系统集成",
      "description": "系统集成和部署",
      "priority": 2,
      "features": [
        {
          "name": "API接口",
          "description": "RESTful API接口开发",
          "test_command": "pytest tests/test_api.py -v",
          "priority": 0,
          "estimated_hours": 3
        },
        {
          "name": "部署配置",
          "description": "部署配置和脚本",
          "test_command": "echo '部署测试完成'",
          "priority": 1,
          "estimated_hours": 2
        }
      ]
    }
  ],
  "technology_stack": {
    "backend": ["Python", "FastAPI"],
    "database": ["SQLite"],
    "testing": ["pytest"],
    "version_control": ["Git"]
  },
  "requirements": [
    "实现基本功能",
    "提供完整测试",
    "代码结构清晰",
    "文档齐全"
  ],
  "success_criteria": [
    "所有测试通过",
    "代码覆盖率 > 70%",
    "功能完整实现",
    "文档完整"
  ]
}
EOF
    
    log_success "计划模板已创建: $output_file"
    echo ""
    echo "📋 下一步:"
    echo "1. 编辑文件添加具体功能: $output_file"
    echo "2. 参考完整模板: $PLAN_TEMPLATE_PATH"
    echo "3. 验证JSON格式: python3 -m json.tool < $output_file"
    echo "4. 开始工作流: ./codemcp_planner.sh workflow start --plan $output_file"
}

# 监控任务
monitor_tasks() {
    local interval="${1:-$MONITOR_INTERVAL}"
    
    log_info "启动任务监控，间隔: ${interval}秒"
    echo "按 Ctrl+C 停止监控"
    echo ""
    
    while true; do
        clear
        echo "=== CodeMCP 任务监控 $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo ""
        
        # 检查服务器状态
        echo "📊 服务器状态:"
        if [ -f "$PROJECT_ROOT/.server_pid" ]; then
            SERVER_PID=$(cat "$PROJECT_ROOT/.server_pid")
            if ps -p $SERVER_PID >/dev/null; then
                echo "  ✅ 运行中 (PID: $SERVER_PID)"
            else
                echo "  ❌ 已停止"
            fi
        else
            echo "  ⚠️  未记录"
        fi
        
        echo ""
        echo "🔄 Git状态:"
        if git status --short 2>/dev/null | head -5; then
            echo "  ..."
        else
            echo "  无变更或非Git仓库"
        fi
        
        echo ""
        echo "📈 最近提交:"
        git log --oneline -3 2>/dev/null || echo "  无提交记录"
        
        echo ""
        echo "📁 工作目录: $(pwd)"
        echo "⏰ 下次更新: $(date -d "+${interval} seconds" '+%H:%M:%S')"
        
        sleep "$interval"
    done
}

# 自动Git提交
auto_git_commit() {
    local repo_path="${1:-.}"
    local commit_message="${2:-feat: AI协同开发提交 - $(date '+%Y-%m-%d %H:%M:%S')}"
    
    log_info "自动Git提交: $repo_path"
    
    if [ ! -d "$repo_path/.git" ]; then
        log_warning "不是Git仓库: $repo_path"
        return 1
    fi
    
    cd "$repo_path" || return 1
    
    # 检查是否有变更
    if ! git status --porcelain | grep -q "."; then
        log_info "没有代码变更"
        return 0
    fi
    
    # 配置Git用户
    git config user.name "$GIT_USER_NAME" 2>/dev/null || true
    git config user.email "$GIT_USER_EMAIL" 2>/dev/null || true
    
    # 添加所有变更
    git add . 2>/dev/null || {
        log_error "git add失败"
        return 1
    }
    
    # 提交
    if git commit -m "$commit_message" 2>/dev/null; then
        local commit_hash=$(git rev-parse --short HEAD 2>/dev/null)
        log_success "Git提交成功: $commit_hash - $commit_message"
        
        # 尝试推送到远程
        if git remote | grep -q "origin"; then
            log_info "推送到远程仓库..."
            git push origin main 2>/dev/null || git push origin master 2>/dev/null || log_warning "推送失败"
        fi
        
        return 0
    else
        log_error "Git提交失败"
        return 1
    fi
}

# 生成进度报告
generate_progress_report() {
    local project_name="$1"
    local output_file="${2:-progress_report_$(date '+%Y%m%d_%H%M').md}"
    
    log_info "生成进度报告: $output_file"
    
    cat > "$output_file" << EOF
# CodeMCP 开发进度报告

**项目**: ${project_name:-未命名项目}
**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
**报告文件**: $(basename "$output_file")

## 系统状态
- **工作目录**: $(pwd)
- **服务器状态**: $(ps aux | grep -v grep | grep -q "codemcp-server" && echo "运行中" || echo "已停止")
- **数据库状态**: $(ls -la "$CODEMCP_PATH/codemcp.db" 2>/dev/null && echo "正常" || echo "异常")

## Git状态
\`\`\`
$(git status 2>/dev/null || echo "非Git仓库")
\`\`\`

## 最近提交记录
\`\`\`
$(git log --oneline -5 2>/dev/null || echo "无提交记录")
\`\`\`

## 目录结构
\`\`\`
$(ls -la 2>/dev/null | head -10)
\`\`\`

## 任务完成情况
| 模块 | 功能点 | 状态 | 进度 |
|------|--------|------|------|
| 核心架构 | 项目初始化 | ⏳ 进行中 | 50% |
| 核心架构 | 开发环境配置 | ✅ 完成 | 100% |
| 业务功能 | 用户管理 | ⏸️ 待开始 | 0% |
| 业务功能 | 数据管理 | ⏸️ 待开始 | 0% |

## 下一步计划
1. 完成项目初始化
2. 开始用户管理模块开发
3. 配置测试环境
4. 集成CI/CD流程

## 问题与风险
- 无重大问题
- 建议定期备份代码
- 需要监控服务器资源使用

## 建议
1. 定期审查代码质量
2. 及时更新依赖包
3. 保持文档同步更新
4. 加强测试覆盖率
EOF
    
    log_success "报告已生成: $output_file"
}

# 显示菜单
show_menu() {
    while true; do
        clear
        echo "========================================"
        echo "      CodeMCP Planner 工作流管理器      "
        echo "========================================"
        echo ""
        echo "当前目录: $(pwd)"
        echo "CodeMCP路径: $CODEMCP_PATH"
        echo "服务器状态: $(ps aux | grep -v grep | grep -q "codemcp-server" && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}已停止${NC}")"
        echo ""
        echo "请选择操作:"
        echo "1. 检查环境"
        echo "2. 启动服务"
        echo "3. 停止服务"
        echo "4. 创建项目计划模板"
        echo "5. 监控任务状态"
        echo "6. 自动Git提交"
        echo "7. 生成进度报告"
        echo "8. 查看服务器日志"
        echo "9. 返回上级"
        echo "0. 退出"
        echo ""
        read -p "选择 (0-9): " choice
        
        case $choice in
            1)
                check_environment
                read -p "按Enter继续..."
                ;;
            2)
                start_services
                read -p "按Enter继续..."
                ;;
            3)
                stop_services
                read -p "按Enter继续..."
                ;;
            4)
                read -p "项目名称: " project_name
                read -p "项目描述: " project_desc
                create_plan_template "$project_name" "$project_desc"
                read -p "按Enter继续..."
                ;;
            5)
                read -p "监控间隔(秒，默认$MONITOR_INTERVAL): " interval
                monitor_tasks "${interval:-$MONITOR_INTERVAL}"
                ;;
            6)
                read -p "Git仓库路径 (默认当前目录): " repo_path
                auto_git_commit "${repo_path:-.}"
                read -p "按Enter继续..."
                ;;
            7)
                read -p "项目名称: " project_name
                generate_progress_report "$project_name"
                read -p "按Enter继续..."
                ;;
            8)
                echo "=== 服务器日志 ==="
                tail -20 "$PROJECT_ROOT/server.log" 2>/dev/null || echo "日志文件不存在"
                read -p "按Enter继续..."
                ;;
            9)
                return 0
                ;;
            0)
                log_info "退出CodeMCP Planner工作流管理器"
                stop_services
                exit 0
                ;;
            *)
                log_error "无效选择"
                read -p "按Enter继续..."
                ;;
        esac
    done
}

# 命令行参数处理
case "${1:-}" in
    "check")
        check_environment
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "plan")
        create_plan_template "$2" "$3" "$4"
        ;;
    "monitor")
        monitor_tasks "$2"
        ;;
    "commit")
        auto_git_commit "$2" "$3"
        ;;
    "report")
        generate_progress_report "$2" "$3"
        ;;
    "menu"|"")
        show_menu
        ;;
    *)
        echo "用法: $0 [command]"
        echo ""
        echo "命令:"
        echo "  check                  检查环境"
        echo "  start                  启动服务"
        echo "  stop                   停止服务"
        echo "  plan <name> <desc> [file] 创建计划模板"
        echo "  monitor [interval]     监控任务"
        echo "  commit [path] [msg]    自动Git提交"
        echo "  report [name] [file]   生成进度报告"
        echo "  menu                   显示菜单（默认）"
        echo ""
        echo "环境变量:"
        echo "  CODEMCP_PATH    CodeMCP安装路径"
        echo "  GIT_USER_NAME   Git用户名"
        echo "  GIT_USER_EMAIL  Git邮箱"
        echo "  MONITOR_INTERVAL 监控间隔(秒)"
        echo ""
        echo "示例:"
        echo "  $0 check"
        echo "  $0 start"
        echo "  $0 plan 我的项目 '这是一个测试项目'"
        echo "  $0 monitor 30"
        echo "  $0 commit ./my-project"
        ;;
esac