#!/usr/bin/env python3
"""
创建博客系统开发计划示例
演示如何使用 CodeMCP Planner Skill
"""

import asyncio
import json
import sys
import os

# 添加父目录到路径，以便导入客户端库
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codemcp_client import CodeMCPPlannerClient, PlanBuilder


async def create_blog_system_plan():
    """创建博客系统开发计划"""
    
    print("=" * 60)
    print("创建博客系统开发计划")
    print("=" * 60)
    
    # 1. 创建客户端
    client = CodeMCPPlannerClient(
        host="localhost",
        port=8000,
        planner_id="openclaw-blog-planner"
    )
    
    try:
        # 2. 连接到服务器
        print("\n1. 连接到 CodeMCP 服务器...")
        websocket = await client.connect()
        
        # 3. 测试连接
        print("\n2. 测试连接...")
        ping_response = await client.ping(websocket)
        if ping_response.get("message_type") == "pong":
            print("   ✅ 连接测试成功")
        else:
            print(f"   ⚠️ 连接测试响应: {ping_response.get('message_type')}")
        
        # 4. 构建博客系统计划
        print("\n3. 构建博客系统计划...")
        
        # 使用 PlanBuilder 创建结构化计划
        blog_plan = PlanBuilder.create_system(
            name="博客系统",
            description="完整的博客平台，支持文章发布、评论、用户管理等功能"
        )
        
        # 添加用户认证模块
        blog_plan = PlanBuilder.add_block(
            blog_plan,
            name="用户认证模块",
            description="用户注册、登录、权限管理",
            priority=0  # 最高优先级
        )
        
        # 为用户认证模块添加功能
        auth_block = blog_plan["blocks"][-1]
        PlanBuilder.add_feature(
            auth_block,
            name="用户注册功能",
            description="新用户注册，支持邮箱和用户名",
            test_command="pytest tests/auth/test_registration.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            auth_block,
            name="用户登录功能",
            description="用户登录验证，支持JWT令牌",
            test_command="pytest tests/auth/test_login.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            auth_block,
            name="密码重置功能",
            description="用户密码重置流程",
            test_command="pytest tests/auth/test_password_reset.py -v",
            priority=1
        )
        
        # 添加文章管理模块
        blog_plan = PlanBuilder.add_block(
            blog_plan,
            name="文章管理模块",
            description="文章创建、编辑、发布、删除",
            priority=1
        )
        
        # 为文章管理模块添加功能
        article_block = blog_plan["blocks"][-1]
        PlanBuilder.add_feature(
            article_block,
            name="文章创建功能",
            description="创建新文章，支持Markdown格式",
            test_command="pytest tests/articles/test_create.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            article_block,
            name="文章编辑功能",
            description="编辑已存在的文章",
            test_command="pytest tests/articles/test_edit.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            article_block,
            name="文章发布功能",
            description="发布文章到公开平台",
            test_command="pytest tests/articles/test_publish.py -v",
            priority=1
        )
        
        # 添加评论系统模块
        blog_plan = PlanBuilder.add_block(
            blog_plan,
            name="评论系统模块",
            description="文章评论、回复、审核",
            priority=2
        )
        
        # 为评论系统模块添加功能
        comment_block = blog_plan["blocks"][-1]
        PlanBuilder.add_feature(
            comment_block,
            name="评论发布功能",
            description="用户发布评论",
            test_command="pytest tests/comments/test_create.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            comment_block,
            name="评论回复功能",
            description="回复其他用户的评论",
            test_command="pytest tests/comments/test_reply.py -v",
            priority=1
        )
        PlanBuilder.add_feature(
            comment_block,
            name="评论审核功能",
            description="管理员审核评论",
            test_command="pytest tests/comments/test_moderation.py -v",
            priority=2
        )
        
        # 添加搜索功能模块
        blog_plan = PlanBuilder.add_block(
            blog_plan,
            name="搜索功能模块",
            description="文章搜索、标签搜索、全文检索",
            priority=3
        )
        
        # 为搜索功能模块添加功能
        search_block = blog_plan["blocks"][-1]
        PlanBuilder.add_feature(
            search_block,
            name="文章搜索功能",
            description="按标题、内容搜索文章",
            test_command="pytest tests/search/test_article_search.py -v",
            priority=0
        )
        PlanBuilder.add_feature(
            search_block,
            name="标签搜索功能",
            description="按标签搜索相关文章",
            test_command="pytest tests/search/test_tag_search.py -v",
            priority=1
        )
        
        # 5. 显示计划结构
        print("\n4. 计划结构概览:")
        print(f"   系统: {blog_plan['system_name']}")
        print(f"   描述: {blog_plan['description']}")
        print(f"   模块数量: {len(blog_plan['blocks'])}")
        
        total_features = 0
        for block in blog_plan["blocks"]:
            print(f"\n   模块: {block['name']} (优先级: {block['priority']})")
            print(f"     描述: {block['description']}")
            print(f"     功能数量: {len(block['features'])}")
            total_features += len(block["features"])
            
            for feature in block["features"]:
                print(f"     - {feature['name']} (优先级: {feature['priority']})")
        
        print(f"\n   总功能数量: {total_features}")
        
        # 6. 发送计划到 CodeMCP
        print("\n5. 发送计划到 CodeMCP 服务器...")
        plan_response = await client.create_plan(
            websocket=websocket,
            system_name=blog_plan["system_name"],
            description=blog_plan["description"],
            blocks=blog_plan["blocks"],
            priority="high"  # 高优先级计划
        )
        
        # 7. 处理响应
        print("\n6. 计划创建响应:")
        if plan_response.get("message_type") == "plan_created":
            print("   ✅ 计划创建成功!")
            plan_id = plan_response.get("data", {}).get("plan_id")
            if plan_id:
                print(f"   计划ID: {plan_id}")
                
                # 获取计划状态
                print("\n7. 获取计划状态...")
                status_response = await client.get_plan_status(websocket, plan_id)
                print(f"   计划状态: {json.dumps(status_response, indent=2)}")
        else:
            print(f"   ⚠️ 计划创建响应: {plan_response.get('message_type')}")
            print(f"   详细响应: {json.dumps(plan_response, indent=2)}")
        
        # 8. 关闭连接
        print("\n8. 关闭连接...")
        await websocket.close()
        print("   ✅ 连接已关闭")
        
        print("\n" + "=" * 60)
        print("博客系统开发计划创建完成!")
        print("=" * 60)
        
        return True
        
    except ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        print("\n请确保:")
        print("1. CodeMCP 服务器正在运行")
        print("2. 服务器地址正确: ws://localhost:8000/mcp/ws/planner")
        print("3. 防火墙允许端口8000")
        return False
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def quick_test():
    """快速测试连接"""
    print("\n快速测试 CodeMCP 连接...")
    
    client = CodeMCPPlannerClient()
    
    try:
        # 测试连接
        websocket = await client.connect()
        
        # 发送ping
        ping_response = await client.ping(websocket)
        print(f"Ping响应: {ping_response.get('message_type')}")
        
        await websocket.close()
        print("✅ 连接测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


if __name__ == "__main__":
    print("CodeMCP Planner Skill - 博客系统开发计划示例")
    print("=" * 60)
    
    # 检查参数
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 快速测试模式
        success = asyncio.run(quick_test())
    else:
        # 完整示例模式
        success = asyncio.run(create_blog_system_plan())
    
    sys.exit(0 if success else 1)