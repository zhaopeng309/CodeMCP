#!/bin/bash
# create_plan_template.sh - 计划模板创建工具

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
PLAN_TEMPLATE_PATH="$CODEMCP_PATH/plan/plan_template.md"
PLAN_DIR="$CODEMCP_PATH/plan"

# 显示帮助
show_help() {
    cat << EOF
用法: create_plan_template.sh [选项]

选项:
  --name <名称>         项目名称（必需）
  --desc <描述>         项目描述
  --output <文件>       输出文件（默认: <名称>_plan.json）
  --format <格式>       输出格式: json, yaml, md（默认: json）
  --validate <文件>     验证计划文件
  --list-templates      列出可用模板
  --show-template       显示计划模板内容
  --help, -h            显示帮助信息

示例:
  # 创建新计划
  create_plan_template.sh --name "用户管理系统" --desc "完整的用户认证系统"
  
  # 验证计划文件
  create_plan_template.sh --validate my_plan.json
  
  # 列出模板
  create_plan_template.sh --list-templates
  
  # 显示模板内容
  create_plan_template.sh --show-template

环境变量:
  CODEMCP_PATH    CodeMCP安装路径
  PLAN_TEMPLATE_PATH 计划模板路径

模板位置: $PLAN_TEMPLATE_PATH
EOF
}

# 检查计划模板
check_plan_templates() {
    log_info "检查计划模板..."
    
    if [ ! -d "$PLAN_DIR" ]; then
        log_error "计划目录不存在: $PLAN_DIR"
        return 1
    fi
    
    echo "计划目录: $PLAN_DIR"
    echo "可用模板:"
    for file in "$PLAN_DIR/"*.md; do
        if [ -f "$file" ]; then
            echo "  $(basename "$file")"
        fi
    done
    
    if [ -f "$PLAN_TEMPLATE_PATH" ]; then
        log_success "主模板文件: $(basename "$PLAN_TEMPLATE_PATH")"
        echo "  大小: $(wc -l < "$PLAN_TEMPLATE_PATH") 行"
        echo "  修改时间: $(stat -c %y "$PLAN_TEMPLATE_PATH")"
    else
        log_error "主模板文件不存在: $PLAN_TEMPLATE_PATH"
        return 1
    fi
    
    return 0
}

# 显示模板内容
show_template_content() {
    if [ ! -f "$PLAN_TEMPLATE_PATH" ]; then
        log_error "模板文件不存在: $PLAN_TEMPLATE_PATH"
        return 1
    fi
    
    log_info "显示计划模板内容: $(basename "$PLAN_TEMPLATE_PATH")"
    echo "========================================"
    head -100 "$PLAN_TEMPLATE_PATH"
    echo "..."
    echo "========================================"
    echo "完整文件: $PLAN_TEMPLATE_PATH"
    echo "总行数: $(wc -l < "$PLAN_TEMPLATE_PATH")"
}

# 创建JSON计划
create_json_plan() {
    local project_name="$1"
    local project_desc="$2"
    local output_file="$3"
    
    log_info "创建JSON计划: $project_name"
    
    cat > "$output_file" << EOF
{
  "system_name": "$project_name",
  "description": "$project_desc",
  "version": "1.0.0",
  "created_at": "$(date -Iseconds)",
  "author": "${GIT_USER_NAME:-AI Developer}",
  "template_source": "$PLAN_TEMPLATE_PATH",
  "blocks": [
    {
      "name": "项目初始化",
      "description": "初始化项目结构和配置",
      "priority": 0,
      "features": [
        {
          "name": "创建项目结构",
          "description": "创建基本的项目目录结构",
          "test_command": "ls -la && echo '项目结构创建完成'",
          "priority": 0,
          "estimated_hours": 1,
          "dependencies": []
        },
        {
          "name": "配置开发环境",
          "description": "配置Python虚拟环境和依赖",
          "test_command": "python3 --version && pip --version && echo '环境配置完成'",
          "priority": 0,
          "estimated_hours": 1,
          "dependencies": ["创建项目结构"]
        }
      ]
    },
    {
      "name": "核心功能开发",
      "description": "开发核心业务功能",
      "priority": 1,
      "features": [
        {
          "name": "实现基础功能",
          "description": "实现项目的基础功能模块",
          "test_command": "pytest tests/test_basic.py -v",
          "priority": 0,
          "estimated_hours": 4,
          "dependencies": ["配置开发环境"]
        },
        {
          "name": "实现业务逻辑",
          "description": "实现具体的业务逻辑",
          "test_command": "pytest tests/test_business.py -v",
          "priority": 1,
          "estimated_hours": 6,
          "dependencies": ["实现基础功能"]
        }
      ]
    },
    {
      "name": "测试与部署",
      "description": "测试和部署相关功能",
      "priority": 2,
      "features": [
        {
          "name": "编写测试用例",
          "description": "编写完整的测试用例",
          "test_command": "pytest tests/ --cov=src --cov-report=html",
          "priority": 0,
          "estimated_hours": 3,
          "dependencies": ["实现业务逻辑"]
        },
        {
          "name": "配置部署",
          "description": "配置部署脚本和环境",
          "test_command": "echo '部署配置测试完成'",
          "priority": 1,
          "estimated_hours": 2,
          "dependencies": ["编写测试用例"]
        }
      ]
    }
  ],
  "technology_stack": {
    "language": ["Python 3.9+"],
    "framework": ["FastAPI"],
    "database": ["SQLite", "PostgreSQL"],
    "testing": ["pytest", "coverage"],
    "tools": ["Git", "Docker", "GitHub Actions"]
  },
  "requirements": [
    "遵循CodeMCP四层数据模型",
    "每个功能点必须有明确的测试命令",
    "设置合理的优先级和依赖关系",
    "提供完整的技术栈信息"
  ],
  "notes": [
    "本计划基于CodeMCP计划模板创建",
    "模板位置: $PLAN_TEMPLATE_PATH",
    "创建时间: $(date '+%Y-%m-%d %H:%M:%S')",
    "使用工具: create_plan_template.sh"
  ]
}
EOF
    
    log_success "JSON计划已创建: $output_file"
}

# 创建Markdown计划
create_markdown_plan() {
    local project_name="$1"
    local project_desc="$2"
    local output_file="$3"
    
    log_info "创建Markdown计划: $project_name"
    
    # 复制模板文件
    if [ -f "$PLAN_TEMPLATE_PATH" ]; then
        cp "$PLAN_TEMPLATE_PATH" "$output_file"
        
        # 替换模板中的占位符
        sed -i "s/\[填写项目名称，如：\"用户认证系统开发\"\]/\"$project_name\"/g" "$output_file"
        sed -i "s/\[简要描述项目目标和范围\]/$project_desc/g" "$output_file"
        
        log_success "Markdown计划已创建: $output_file"
        echo "基于模板: $PLAN_TEMPLATE_PATH"
    else
        log_error "模板文件不存在，无法创建Markdown计划"
        return 1
    fi
}

# 验证计划文件
validate_plan_file() {
    local plan_file="$1"
    
    if [ ! -f "$plan_file" ]; then
        log_error "计划文件不存在: $plan_file"
        return 1
    fi
    
    log_info "验证计划文件: $plan_file"
    
    # 检查文件类型
    local file_ext="${plan_file##*.}"
    
    case "$file_ext" in
        json)
            # 验证JSON格式
            if command -v python3 >/dev/null 2>&1; then
                if python3 -m json.tool "$plan_file" >/dev/null; then
                    log_success "JSON格式验证通过"
                    
                    # 检查必需字段
                    if grep -q '"system_name"' "$plan_file" && \
                       grep -q '"description"' "$plan_file" && \
                       grep -q '"blocks"' "$plan_file"; then
                        log_success "必需字段检查通过"
                    else
                        log_warning "缺少某些必需字段"
                    fi
                    
                    # 统计信息
                    echo "计划统计:"
                    echo "  文件大小: $(wc -c < "$plan_file") 字节"
                    echo "  行数: $(wc -l < "$plan_file")"
                    echo "  blocks数量: $(grep -c '"name"' "$plan_file" | head -1)"
                    
                else
                    log_error "JSON格式验证失败"
                    return 1
                fi
            else
                log_warning "Python3未安装，跳过JSON验证"
            fi
            ;;
        md|markdown)
            # 验证Markdown格式
            log_info "Markdown文件验证"
            echo "文件类型: Markdown"
            echo "文件大小: $(wc -c < "$plan_file") 字节"
            echo "行数: $(wc -l < "$plan_file")"
            
            # 检查关键章节
            local has_sections=0
            grep -q "# " "$plan_file" && has_sections=$((has_sections + 1))
            grep -q "## " "$plan_file" && has_sections=$((has_sections + 1))
            
            if [ $has_sections -ge 2 ]; then
                log_success "Markdown结构基本完整"
            else
                log_warning "Markdown结构可能不完整"
            fi
            ;;
        yaml|yml)
            # 验证YAML格式
            if command -v python3 >/dev/null 2>&1; then
                if python3 -c "import yaml; yaml.safe_load(open('$plan_file'))" >/dev/null 2>&1; then
                    log_success "YAML格式验证通过"
                else
                    log_error "YAML格式验证失败"
                    return 1
                fi
            else
                log_warning "Python3未安装，跳过YAML验证"
            fi
            ;;
        *)
            log_warning "未知文件类型: .$file_ext"
            echo "支持的类型: .json, .md, .markdown, .yaml, .yml"
            ;;
    esac
    
    return 0
}

# 主函数
main() {
    local project_name=""
    local project_desc=""
    local output_file=""
    local format="json"
    local validate_file=""
    local list_templates=false
    local show_template=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)
                project_name="$2"
                shift 2
                ;;
            --desc|--description)
                project_desc="$2"
                shift 2
                ;;
            --output)
                output_file="$2"
                shift 2
                ;;
            --format)
                format="$2"
                shift 2
                ;;
            --validate)
                validate_file="$2"
                shift 2
                ;;
            --list-templates)
                list_templates=true
                shift
                ;;
            --show-template)
                show_template=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查计划模板
    check_plan_templates || exit 1
    
    # 处理不同操作
    if [ -n "$validate_file" ]; then
        validate_plan_file "$validate_file"
        exit $?
    elif [ "$list_templates" = true ]; then
        exit 0
    elif [ "$show_template" = true ]; then
        show_template_content
        exit 0
    elif [ -z "$project_name" ]; then
        log_error "必须提供项目名称 (--name)"
        show_help
        exit 1
    fi
    
    # 设置默认值
    project_desc="${project_desc:-$project_name 开发项目}"
    output_file="${output_file:-${project_name}_plan.${format}}"
    
    # 创建计划
    log_info "开始创建计划..."
    echo "项目名称: $project_name"
    echo "项目描述: $project_desc"
    echo "输出格式: $format"
    echo "输出文件: $output_file"
    echo "模板位置: $PLAN_TEMPLATE_PATH"
    echo ""
    
    case "$format" in
        json)
            create_json_plan "$project_name" "$project_desc" "$output_file"
            ;;
        md|markdown)
            create_markdown_plan "$project_name" "$project_desc" "$output_file"
            ;;
        yaml|yml)
            log_warning "YAML格式暂未实现，创建JSON格式"
            output_file="${output_file%.*}.json"
            create_json_plan "$project_name" "$project_desc" "$output_file"
            ;;
        *)
            log_error "不支持的格式: $format"
            echo "支持格式: json, md, markdown"
            exit 1
            ;;
    esac
    
    # 验证创建的文件
    echo ""
    log_info "验证创建的计划文件..."
    validate_plan_file "$output_file"
    
    # 显示下一步建议
    echo ""
    echo "🎯 下一步建议:"
    echo "1. 编辑计划文件: $output_file"
    echo "2. 添加具体功能和测试命令"
    echo "3. 设置合理的优先级和依赖关系"
    echo "4. 参考完整模板: $PLAN_TEMPLATE_PATH"
    echo "5. 开始工作流: codemcp-planner workflow start --plan $output_file"
    echo ""
    echo "📋 计划模板位置: $PLAN_TEMPLATE_PATH"
    echo "📁 计划目录: $PLAN_DIR"
}

# 运行主函数
main "$@"