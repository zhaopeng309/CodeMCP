#!/usr/bin/env python3
"""
初始化管理员用户脚本

用于创建默认的管理员用户。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.codemcp.config import settings
from src.codemcp.database.session import AsyncSessionFactory, init_db
from src.codemcp.models.user import User
from src.codemcp.utils.password import get_password_hash
from sqlalchemy import select


async def init_admin_user():
    """初始化管理员用户"""
    print("正在初始化数据库表...")
    
    # 创建数据库表
    await init_db()
    
    print("正在检查管理员用户...")
    
    # 使用会话工厂创建会话
    async with AsyncSessionFactory() as db:
        # 检查是否已存在管理员用户
        result = await db.execute(
            select(User).where(User.username == settings.admin_username)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"管理员用户 '{settings.admin_username}' 已存在")
            print(f"用户ID: {existing_admin.id}")
            print(f"邮箱: {existing_admin.email}")
            print(f"是否超级用户: {existing_admin.is_superuser}")
            return
        
        # 创建管理员用户
        hashed_password = get_password_hash(settings.admin_password)
        admin_user = User(
            username=settings.admin_username,
            email=settings.admin_email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        print(f"✅ 管理员用户创建成功!")
        print(f"   用户名: {admin_user.username}")
        print(f"   邮箱: {admin_user.email}")
        print(f"   用户ID: {admin_user.id}")
        print(f"   是否超级用户: {admin_user.is_superuser}")
        print("\n⚠️  重要提示: 请立即修改默认密码!")
        print(f"   默认密码: {settings.admin_password}")
        print("   建议通过 /auth/me 端点修改密码")


async def list_users():
    """列出所有用户"""
    print("正在列出所有用户...")
    
    # 使用会话工厂创建会话
    async with AsyncSessionFactory() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("数据库中没有用户")
            return
        
        print(f"找到 {len(users)} 个用户:")
        print("-" * 80)
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"是否激活: {user.is_active}")
            print(f"是否超级用户: {user.is_superuser}")
            print(f"创建时间: {user.created_at}")
            print("-" * 80)


async def main():
    """主函数"""
    print("=" * 60)
    print("CodeMCP 管理员用户初始化工具")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        await list_users()
    else:
        await init_admin_user()
    
    print("\n✅ 初始化完成")


if __name__ == "__main__":
    asyncio.run(main())