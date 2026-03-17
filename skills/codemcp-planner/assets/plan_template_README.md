# 计划模板说明

## 模板位置

CodeMCP 的计划模板位于：
```
/home/designer/tools/CodeMCP/plan/
```

### 主要模板文件
1. **plan_template.md** - 完整的项目计划编写模板
2. **codemcp_plan_1.0.md** - CodeMCP 1.0版本计划规范

## 使用方式

### 方式1：直接使用CodeMCP模板
```bash
# 查看计划模板
cat /home/designer/tools/CodeMCP/plan/plan_template.md

# 基于模板创建计划
cp /home/designer/tools/CodeMCP/plan/plan_template.md my_project_plan.md
# 然后编辑my_project_plan.md文件
```

### 方式2：使用技能包工具
```bash
# 使用create_plan_template.sh脚本
./scripts/create_plan_template.sh --name "我的项目" --output my_plan.json

# 脚本会自动引用正确的模板位置
```

### 方式3：手动创建JSON计划
```json
{
  "system_name": "项目名称",
  "description": "项目描述",
  "blocks": [
    {
      "name": "模块名称",
      "description": "模块描述",
      "features": [
        {
          "name": "功能名称",
          "description": "功能描述",
          "test_command": "测试命令"
        }
      ]
    }
  ]
}
```

## 模板结构

### 四层数据模型
1. **System（系统）** - 项目实例
2. **Block（模块）** - 功能模块
3. **Feature（功能）** - 具体功能点
4. **Test（测试）** - 验证单元

### 必需字段
- `system_name`: 系统名称
- `description`: 系统描述
- `blocks`: 模块数组
  - `name`: 模块名称
  - `description`: 模块描述
  - `features`: 功能数组
    - `name`: 功能名称
    - `description`: 功能描述
    - `test_command`: 测试命令

### 可选字段
- `version`: 计划版本
- `author`: 作者
- `created_at`: 创建时间
- `technology_stack`: 技术栈
- `requirements`: 需求列表
- `success_criteria`: 成功标准

## 验证计划

### 使用Python验证JSON格式
```bash
python3 -m json.tool < plan.json
```

### 使用技能包验证
```bash
./scripts/create_plan_template.sh --validate plan.json
```

## 示例

查看 `examples/` 目录中的示例计划：
- `project_plan_template.json` - 完整的项目计划示例
- `basic_workflow/` - 基础工作流示例

## 注意事项

1. **测试命令必须可执行**：每个功能点必须有明确的、可执行的测试命令
2. **依赖关系明确**：标记任务间的依赖关系
3. **优先级合理**：数字越小优先级越高（0为最高）
4. **时间估算合理**：提供合理的时间估算
5. **技术栈匹配**：确保技术栈与项目需求匹配

## 问题解决

如果遇到计划模板相关问题：

1. 检查模板文件是否存在：`ls -la /home/designer/tools/CodeMCP/plan/`
2. 验证JSON格式：`python3 -m json.tool < plan.json`
3. 使用问题报告：`./scripts/problem_report.sh --type "计划模板"`

## 更新日志

- 2026-03-17: 初始版本，指向正确的计划模板位置
- 模板版本: CodeMCP Plan 1.0