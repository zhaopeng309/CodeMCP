#!/usr/bin/env python3
"""
需求分析器模块
将自然语言需求转换为CodeMCP四层数据模型的结构化计划
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class RequirementsAnalyzer:
    """需求分析器 - 将自然语言需求转换为结构化计划"""
    
    def __init__(self):
        self.common_patterns = {
            "用户管理": ["用户", "注册", "登录", "认证", "权限", "角色", "密码"],
            "数据管理": ["数据库", "存储", "CRUD", "增删改查", "模型", "表"],
            "API接口": ["API", "接口", "REST", "端点", "路由", "请求"],
            "前端界面": ["界面", "UI", "前端", "页面", "组件", "交互"],
            "测试验证": ["测试", "验证", "单元测试", "集成测试", "自动化"],
            "部署运维": ["部署", "运维", "监控", "日志", "性能", "安全"]
        }
        
        self.feature_templates = {
            "用户注册功能": {
                "description": "新用户注册流程",
                "test_command": "pytest tests/auth/test_registration.py -v",
                "priority": 0
            },
            "用户登录功能": {
                "description": "用户登录验证",
                "test_command": "pytest tests/auth/test_login.py -v",
                "priority": 0
            },
            "数据创建功能": {
                "description": "创建新数据记录",
                "test_command": "pytest tests/data/test_create.py -v",
                "priority": 0
            },
            "数据查询功能": {
                "description": "查询数据记录",
                "test_command": "pytest tests/data/test_query.py -v",
                "priority": 0
            },
            "API端点功能": {
                "description": "提供API端点",
                "test_command": "pytest tests/api/test_endpoints.py -v",
                "priority": 0
            },
            "界面组件功能": {
                "description": "前端界面组件",
                "test_command": "pytest tests/ui/test_components.py -v",
                "priority": 1
            }
        }
    
    def analyze_requirements(self, requirements_text: str) -> Dict[str, Any]:
        """
        分析自然语言需求，生成结构化计划
        
        Args:
            requirements_text: 自然语言需求描述
            
        Returns:
            结构化计划字典
        """
        print("🔍 分析用户需求...")
        
        # 提取关键信息
        system_name = self._extract_system_name(requirements_text)
        description = self._summarize_description(requirements_text)
        
        # 识别模块
        blocks = self._identify_blocks(requirements_text)
        
        # 为每个模块识别功能
        for block in blocks:
            block["features"] = self._identify_features_for_block(block["name"], requirements_text)
        
        # 构建计划结构
        plan = {
            "system_name": system_name,
            "description": description,
            "blocks": blocks,
            "analysis_metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "requirements_length": len(requirements_text),
                "blocks_count": len(blocks),
                "total_features": sum(len(block["features"]) for block in blocks)
            }
        }
        
        return plan
    
    def _extract_system_name(self, text: str) -> str:
        """从需求文本中提取系统名称"""
        # 查找常见的系统名称模式
        patterns = [
            r'开发(?:一个|一套)?([^，。,.!！?？\n]+)(?:系统|平台|应用)',
            r'创建(?:一个|一套)?([^，。,.!！?？\n]+)(?:系统|平台|应用)',
            r'实现(?:一个|一套)?([^，。,.!！?？\n]+)(?:系统|平台|应用)',
            r'([^，。,.!！?？\n]+)(?:系统|平台|应用)的开发'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:
                    return name
        
        # 如果没有找到，使用默认名称
        return "智能开发项目"
    
    def _summarize_description(self, text: str) -> str:
        """生成系统描述摘要"""
        # 提取前100个字符作为摘要
        if len(text) > 100:
            summary = text[:100] + "..."
        else:
            summary = text
        
        return f"基于用户需求开发的系统。需求摘要：{summary}"
    
    def _identify_blocks(self, text: str) -> List[Dict[str, Any]]:
        """识别需求中的模块"""
        blocks = []
        identified_categories = set()
        
        # 检查每个常见模式
        for category, keywords in self.common_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    if category not in identified_categories:
                        blocks.append({
                            "name": f"{category}",
                            "description": f"负责{category}相关功能",
                            "priority": len(blocks),  # 按识别顺序设置优先级
                            "features": []
                        })
                        identified_categories.add(category)
                    break
        
        # 如果没有识别到任何模块，添加默认模块
        if not blocks:
            blocks = [
                {
                    "name": "核心功能模块",
                    "description": "系统核心功能实现",
                    "priority": 0,
                    "features": []
                },
                {
                    "name": "数据管理模块",
                    "description": "数据存储和管理功能",
                    "priority": 1,
                    "features": []
                },
                {
                    "name": "用户界面模块",
                    "description": "用户界面和交互功能",
                    "priority": 2,
                    "features": []
                }
            ]
        
        return blocks
    
    def _identify_features_for_block(self, block_name: str, text: str) -> List[Dict[str, Any]]:
        """为模块识别功能"""
        features = []
        
        # 根据模块名称选择功能模板
        if "用户" in block_name or "认证" in block_name:
            features.extend([
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
                }
            ])
        
        if "数据" in block_name or "存储" in block_name:
            features.extend([
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
                }
            ])
        
        if "API" in block_name or "接口" in block_name:
            features.extend([
                {
                    "name": "API端点功能",
                    "description": "提供API端点",
                    "test_command": "pytest tests/api/test_endpoints.py -v",
                    "priority": 0
                }
            ])
        
        if "界面" in block_name or "前端" in block_name or "UI" in block_name:
            features.extend([
                {
                    "name": "界面组件功能",
                    "description": "前端界面组件",
                    "test_command": "pytest tests/ui/test_components.py -v",
                    "priority": 1
                }
            ])
        
        # 如果没有匹配的功能，添加通用功能
        if not features:
            features.append({
                "name": f"{block_name}核心功能",
                "description": f"{block_name}的核心功能实现",
                "test_command": f"pytest tests/{block_name}/test_core.py -v",
                "priority": 0
            })
        
        return features
    
    def refine_plan_based_on_failure(self, original_plan: Dict[str, Any], 
                                    failed_features: List[str]) -> Dict[str, Any]:
        """
        基于失败的功能重新规划，细化功能颗粒度
        
        Args:
            original_plan: 原始计划
            failed_features: 失败的功能名称列表
            
        Returns:
            细化后的新计划
        """
        print("🔄 基于失败功能重新规划...")
        
        refined_plan = original_plan.copy()
        
        # 查找失败功能所在的模块
        for block in refined_plan["blocks"]:
            for feature in block["features"][:]:  # 使用副本遍历
                if feature["name"] in failed_features:
                    print(f"   细化失败功能: {feature['name']}")
                    
                    # 移除失败的功能
                    block["features"].remove(feature)
                    
                    # 添加更细粒度的功能
                    refined_features = self._refine_feature(feature)
                    block["features"].extend(refined_features)
        
        # 更新元数据
        refined_plan["analysis_metadata"]["refined_at"] = datetime.now().isoformat()
        refined_plan["analysis_metadata"]["refined_reason"] = f"功能失败: {', '.join(failed_features)}"
        
        return refined_plan
    
    def _refine_feature(self, feature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将功能细化为更小的子功能"""
        feature_name = feature["name"]
        
        if "用户注册" in feature_name:
            return [
                {
                    "name": "邮箱验证功能",
                    "description": "用户邮箱验证流程",
                    "test_command": "pytest tests/auth/test_email_verification.py -v",
                    "priority": feature.get("priority", 0)
                },
                {
                    "name": "表单验证功能",
                    "description": "注册表单数据验证",
                    "test_command": "pytest tests/auth/test_form_validation.py -v",
                    "priority": feature.get("priority", 0)
                },
                {
                    "name": "用户数据存储功能",
                    "description": "用户数据存储到数据库",
                    "test_command": "pytest tests/auth/test_user_storage.py -v",
                    "priority": feature.get("priority", 0)
                }
            ]
        
        elif "用户登录" in feature_name:
            return [
                {
                    "name": "密码验证功能",
                    "description": "用户密码验证",
                    "test_command": "pytest tests/auth/test_password_verification.py -v",
                    "priority": feature.get("priority", 0)
                },
                {
                    "name": "会话管理功能",
                    "description": "用户会话创建和管理",
                    "test_command": "pytest tests/auth/test_session_management.py -v",
                    "priority": feature.get("priority", 0)
                },
                {
                    "name": "安全令牌功能",
                    "description": "安全令牌生成和验证",
                    "test_command": "pytest tests/auth/test_security_tokens.py -v",
                    "priority": feature.get("priority", 0)
                }
            ]
        
        elif "数据创建" in feature_name:
            return [
                {
                    "name": "数据验证功能",
                    "description": "创建数据前的验证",
                    "test_command": "pytest tests/data/test_validation.py -v",
                    "priority": feature.get("priority", 0)
                },
                {
                    "name": "数据存储功能",
                    "description": "数据存储到数据库",
                    "test_command": "pytest tests/data/test_storage.py -v",
                    "priority": feature.get("priority", 0)
                },
                {
                    "name": "数据关联功能",
                    "description": "处理数据关联关系",
                    "test_command": "pytest tests/data/test_relationships.py -v",
                    "priority": feature.get("priority", 0)
                }
            ]
        
        # 默认细化：将功能拆分为3个子功能
        return [
            {
                "name": f"{feature_name} - 子功能1",
                "description": f"{feature['description']} - 第一部分",
                "test_command": feature["test_command"].replace(".py", "_part1.py"),
                "priority": feature.get("priority", 0)
            },
            {
                "name": f"{feature_name} - 子功能2",
                "description": f"{feature['description']} - 第二部分",
                "test_command": feature["test_command"].replace(".py", "_part2.py"),
                "priority": feature.get("priority", 0)
            },
            {
                "name": f"{feature_name} - 子功能3",
                "description": f"{feature['description']} - 第三部分",
                "test_command": feature["test_command"].replace(".py", "_part3.py"),
                "priority": feature.get("priority", 0)
            }
        ]


def example_usage():
    """使用示例"""
    analyzer = RequirementsAnalyzer()
    
    # 示例需求
    requirements = """
    我需要开发一个博客系统，要求有用户注册登录功能，
    可以发布和管理文章，支持评论功能，还需要搜索功能。
    系统要稳定可靠，界面要美观。
    """
    
    # 分析需求
    plan = analyzer.analyze_requirements(requirements)
    
    print("📋 分析结果:")
    print(f"系统名称: {plan['system_name']}")
    print(f"描述: {plan['description']}")
    print(f"模块数量: {len(plan['blocks'])}")
    
    for i, block in enumerate(plan["blocks"], 1):
        print(f"\n模块 {i}: {block['name']}")
        print(f"  描述: {block['description']}")
        print(f"  功能数量: {len(block['features'])}")
        
        for j, feature in enumerate(block["features"], 1):
            print(f"  功能 {j}: {feature['name']}")
            print(f"    测试命令: {feature['test_command']}")
    
    # 模拟失败后重新规划
    print("\n🔄 模拟失败后重新规划...")
    failed_features = ["用户注册功能"]
    refined_plan = analyzer.refine_plan_based_on_failure(plan, failed_features)
    
    print(f"细化后总功能数量: {sum(len(block['features']) for block in refined_plan['blocks'])}")


if __name__ == "__main__":
    example_usage()