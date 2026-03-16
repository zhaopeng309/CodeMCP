#!/usr/bin/env python3
"""
计划模板模块

提供预定义的计划模板，用于快速创建常见类型的开发计划。
"""

from typing import Dict, List, Any


class PlanTemplates:
    """计划模板集合"""

    @staticmethod
    def web_application(name: str, description: str = "") -> Dict[str, Any]:
        """Web应用程序模板"""
        return {
            "system_name": name,
            "description": description or f"{name} Web应用程序",
            "blocks": [
                {
                    "name": "用户认证模块",
                    "description": "用户注册、登录、认证功能",
                    "priority": 0,
                    "features": [
                        {
                            "name": "用户注册功能",
                            "description": "新用户注册流程",
                            "test_command": "pytest tests/auth/test_registration.py -v",
                            "priority": 0
                        },
                        {
                            "name": "用户登录功能",
                            "description": "用户登录验证",
                            "test_command": "pytest tests/auth/test_login.py -v",
                            "priority": 0
                        },
                        {
                            "name": "密码重置功能",
                            "description": "用户密码重置流程",
                            "test_command": "pytest tests/auth/test_password_reset.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "数据管理模块",
                    "description": "数据存储和管理功能",
                    "priority": 1,
                    "features": [
                        {
                            "name": "数据创建功能",
                            "description": "创建新数据记录",
                            "test_command": "pytest tests/data/test_create.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据查询功能",
                            "description": "查询数据记录",
                            "test_command": "pytest tests/data/test_query.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据更新功能",
                            "description": "更新数据记录",
                            "test_command": "pytest tests/data/test_update.py -v",
                            "priority": 1
                        },
                        {
                            "name": "数据删除功能",
                            "description": "删除数据记录",
                            "test_command": "pytest tests/data/test_delete.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "API接口模块",
                    "description": "REST API接口功能",
                    "priority": 2,
                    "features": [
                        {
                            "name": "用户API端点",
                            "description": "用户相关API端点",
                            "test_command": "pytest tests/api/test_user_endpoints.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据API端点",
                            "description": "数据相关API端点",
                            "test_command": "pytest tests/api/test_data_endpoints.py -v",
                            "priority": 0
                        },
                        {
                            "name": "API认证中间件",
                            "description": "API请求认证中间件",
                            "test_command": "pytest tests/api/test_auth_middleware.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "前端界面模块",
                    "description": "用户界面和交互功能",
                    "priority": 3,
                    "features": [
                        {
                            "name": "用户界面组件",
                            "description": "可复用UI组件",
                            "test_command": "pytest tests/ui/test_components.py -v",
                            "priority": 0
                        },
                        {
                            "name": "页面路由功能",
                            "description": "页面路由和导航",
                            "test_command": "pytest tests/ui/test_routing.py -v",
                            "priority": 0
                        },
                        {
                            "name": "表单处理功能",
                            "description": "表单输入和处理",
                            "test_command": "pytest tests/ui/test_forms.py -v",
                            "priority": 1
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def cli_tool(name: str, description: str = "") -> Dict[str, Any]:
        """命令行工具模板"""
        return {
            "system_name": name,
            "description": description or f"{name} 命令行工具",
            "blocks": [
                {
                    "name": "命令解析模块",
                    "description": "命令行参数解析功能",
                    "priority": 0,
                    "features": [
                        {
                            "name": "参数解析功能",
                            "description": "解析命令行参数",
                            "test_command": "pytest tests/cli/test_arg_parse.py -v",
                            "priority": 0
                        },
                        {
                            "name": "子命令支持",
                            "description": "支持子命令结构",
                            "test_command": "pytest tests/cli/test_subcommands.py -v",
                            "priority": 0
                        },
                        {
                            "name": "帮助文档生成",
                            "description": "自动生成帮助文档",
                            "test_command": "pytest tests/cli/test_help.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "核心功能模块",
                    "description": "工具核心功能",
                    "priority": 1,
                    "features": [
                        {
                            "name": "核心处理逻辑",
                            "description": "工具核心处理逻辑",
                            "test_command": "pytest tests/core/test_processor.py -v",
                            "priority": 0
                        },
                        {
                            "name": "文件处理功能",
                            "description": "文件读写和处理",
                            "test_command": "pytest tests/core/test_file_io.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据转换功能",
                            "description": "数据格式转换",
                            "test_command": "pytest tests/core/test_data_conversion.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "输出模块",
                    "description": "结果输出和格式化",
                    "priority": 2,
                    "features": [
                        {
                            "name": "控制台输出",
                            "description": "控制台输出格式化",
                            "test_command": "pytest tests/output/test_console.py -v",
                            "priority": 0
                        },
                        {
                            "name": "文件输出",
                            "description": "结果输出到文件",
                            "test_command": "pytest tests/output/test_file_output.py -v",
                            "priority": 0
                        },
                        {
                            "name": "报告生成",
                            "description": "生成执行报告",
                            "test_command": "pytest tests/output/test_report.py -v",
                            "priority": 1
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def library(name: str, description: str = "") -> Dict[str, Any]:
        """代码库/库模板"""
        return {
            "system_name": name,
            "description": description or f"{name} 代码库",
            "blocks": [
                {
                    "name": "核心算法模块",
                    "description": "核心算法和逻辑",
                    "priority": 0,
                    "features": [
                        {
                            "name": "核心算法实现",
                            "description": "核心算法实现",
                            "test_command": "pytest tests/algorithms/test_core.py -v",
                            "priority": 0
                        },
                        {
                            "name": "性能优化",
                            "description": "算法性能优化",
                            "test_command": "pytest tests/algorithms/test_performance.py -v",
                            "priority": 1
                        },
                        {
                            "name": "边界条件处理",
                            "description": "处理边界条件",
                            "test_command": "pytest tests/algorithms/test_edge_cases.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "工具函数模块",
                    "description": "实用工具函数",
                    "priority": 1,
                    "features": [
                        {
                            "name": "字符串处理函数",
                            "description": "字符串处理工具函数",
                            "test_command": "pytest tests/utils/test_strings.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据处理函数",
                            "description": "数据处理工具函数",
                            "test_command": "pytest tests/utils/test_data.py -v",
                            "priority": 0
                        },
                        {
                            "name": "日期时间函数",
                            "description": "日期时间处理函数",
                            "test_command": "pytest tests/utils/test_datetime.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "接口适配器模块",
                    "description": "外部接口适配器",
                    "priority": 2,
                    "features": [
                        {
                            "name": "API客户端",
                            "description": "外部API客户端",
                            "test_command": "pytest tests/adapters/test_api_client.py -v",
                            "priority": 0
                        },
                        {
                            "name": "文件格式适配器",
                            "description": "不同文件格式支持",
                            "test_command": "pytest tests/adapters/test_file_formats.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据库适配器",
                            "description": "数据库连接适配器",
                            "test_command": "pytest tests/adapters/test_database.py -v",
                            "priority": 1
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def api_server(name: str, description: str = "") -> Dict[str, Any]:
        """API服务器模板"""
        return {
            "system_name": name,
            "description": description or f"{name} API服务器",
            "blocks": [
                {
                    "name": "API端点模块",
                    "description": "REST API端点",
                    "priority": 0,
                    "features": [
                        {
                            "name": "用户管理端点",
                            "description": "用户相关API端点",
                            "test_command": "pytest tests/api/test_user_endpoints.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据操作端点",
                            "description": "数据CRUD API端点",
                            "test_command": "pytest tests/api/test_data_endpoints.py -v",
                            "priority": 0
                        },
                        {
                            "name": "搜索查询端点",
                            "description": "搜索和查询API端点",
                            "test_command": "pytest tests/api/test_search_endpoints.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "业务逻辑模块",
                    "description": "业务逻辑处理",
                    "priority": 1,
                    "features": [
                        {
                            "name": "业务规则引擎",
                            "description": "业务规则处理",
                            "test_command": "pytest tests/business/test_rules.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据验证逻辑",
                            "description": "数据验证和清洗",
                            "test_command": "pytest tests/business/test_validation.py -v",
                            "priority": 0
                        },
                        {
                            "name": "工作流引擎",
                            "description": "业务流程工作流",
                            "test_command": "pytest tests/business/test_workflow.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "数据访问模块",
                    "description": "数据存储和访问",
                    "priority": 2,
                    "features": [
                        {
                            "name": "数据库访问层",
                            "description": "数据库CRUD操作",
                            "test_command": "pytest tests/data/test_dao.py -v",
                            "priority": 0
                        },
                        {
                            "name": "缓存层",
                            "description": "数据缓存功能",
                            "test_command": "pytest tests/data/test_cache.py -v",
                            "priority": 0
                        },
                        {
                            "name": "数据迁移",
                            "description": "数据迁移和版本控制",
                            "test_command": "pytest tests/data/test_migrations.py -v",
                            "priority": 1
                        }
                    ]
                },
                {
                    "name": "安全认证模块",
                    "description": "安全和认证功能",
                    "priority": 3,
                    "features": [
                        {
                            "name": "JWT认证",
                            "description": "JWT令牌认证",
                            "test_command": "pytest tests/security/test_jwt.py -v",
                            "priority": 0
                        },
                        {
                            "name": "权限控制",
                            "description": "角色和权限控制",
                            "test_command": "pytest tests/security/test_permissions.py -v",
                            "priority": 0
                        },
                        {
                            "name": "请求限流",
                            "description": "API请求限流",
                            "test_command": "pytest tests/security/test_rate_limit.py -v",
                            "priority": 1
                        }
                    ]
                }
            ]
        }


def get_template(template_name: str, **kwargs) -> Dict[str, Any]:
    """获取指定模板"""
    templates = {
        "web_application": PlanTemplates.web_application,
        "cli_tool": PlanTemplates.cli_tool,
        "library": PlanTemplates.library,
        "api_server": PlanTemplates.api_server,
    }

    if template_name not in templates:
        raise ValueError(f"未知模板: {template_name}。可用模板: {', '.join(templates.keys())}")

    return templates[template_name](**kwargs)


def list_templates() -> List[str]:
    """列出所有可用模板"""
    return ["web_application", "cli_tool", "library", "api_server"]


if __name__ == "__main__":
    # 示例用法
    print("可用的计划模板:")
    for template in list_templates():
        print(f"  - {template}")

    print("\nWeb应用程序模板示例:")
    web_app = get_template("web_application", name="博客系统", description="个人博客系统")
    print(f"  系统: {web_app['system_name']}")
    print(f"  模块数: {len(web_app['blocks'])}")
    print(f"  总功能数: {sum(len(block['features']) for block in web_app['blocks'])}")