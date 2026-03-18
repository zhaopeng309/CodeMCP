#!/usr/bin/env python3
"""
重置管理员密码脚本

用于重置 CodeMCP 系统中 admin 用户的密码。
当默认密码无效或忘记密码时使用。
"""

import asyncio
import sys
from src.codemcp.database.session import AsyncSessionFactory
from src.codemcp.models.user import User
from src.codemcp.utils.password import get_password_hash
from sqlalchemy import select, update

async def reset_admin_password(new_password: str = "Admin@123456"):
    """重置管理员密码
    
    Args:
        new_password: 新密码，默认为 "Admin@123456"
    """
    print(f"正在重置管理员密码...")
    print(f"新密码: {new_password}")
    
    async with AsyncSessionFactory() as db:
        # 检查管理员用户是否存在
        result = await db.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()
        
        if not user:
            print("错误: 未找到管理员用户 'admin'")
            return False
        
        print(f"找到管理员用户: {user.username}")
        print(f"当前密码哈希: {user.hashed_password[:30]}...")
        
        # 生成新密码哈希
        new_hashed_password = get_password_hash(new_password)
        print(f"新密码哈希: {new_hashed_password[:30]}...")
        
        # 更新密码
        await db.execute(
            update(User)
            .where(User.username == 'admin')
            .values(hashed_password=new_hashed_password)
        )
        await db.commit()
        
        print("✓ 密码已更新")
        
        # 验证新密码
        from src.codemcp.utils.password import verify_password
        verify_result = verify_password(new_password, new_hashed_password)
        print(f"✓ 新密码验证: {verify_result}")
        
        return True

async def main():
    """主函数"""
    print("=" * 50)
    print("CodeMCP 管理员密码重置工具")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
        if len(new_password) < 8:
            print("错误: 密码必须至少8个字符")
            return
        if not any(c.isdigit() for c in new_password):
            print("警告: 建议密码包含数字")
        if not any(c.isalpha() for c in new_password):
            print("警告: 建议密码包含字母")
    else:
        # 使用默认强密码
        new_password = "Admin@123456"
        print(f"使用默认强密码: {new_password}")
        print("提示: 可以传递自定义密码作为参数: python reset_admin_password.py 'YourNewPassword'")
    
    print()
    
    try:
        success = await reset_admin_password(new_password)
        if success:
            print("\n" + "=" * 50)
            print("密码重置成功!")
            print("=" * 50)
            print(f"用户名: admin")
            print(f"密码: {new_password}")
            print("\n使用以下命令登录:")
            print(f"  ./bin/codemcp user login")
            print("\n登录后建议立即修改密码:")
            print(f"  ./bin/codemcp user change-password")
        else:
            print("\n密码重置失败")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())