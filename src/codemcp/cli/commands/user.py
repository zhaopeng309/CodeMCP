"""
管理员账户管理命令

管理唯一的系统管理员账户，包括登录、密码修改和token保存功能。
系统只有一个管理员账户（admin），不支持多用户管理。
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from src.codemcp.config import Settings, ensure_project_config
from src.codemcp.database.session import AsyncSessionFactory
from src.codemcp.models.user import User
from src.codemcp.utils.password import get_password_hash
from src.codemcp.utils.jwt import create_token

app = typer.Typer(
    name="user",
    help="管理员账户管理（系统只有一个管理员账户）",
    no_args_is_help=True,
)

console = Console()


def _save_user_token_to_config(user: User, token: str) -> bool:
    """将管理员token保存到配置文件
    
    支持配置文件存储管理员token，用于自动认证
    """
    try:
        # 确保项目配置文件存在
        config_path = ensure_project_config()
        
        # 读取现有配置
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 查找或添加管理员token配置
        admin_token_found = False
        admin_token_prefix = "USER_TOKEN_ADMIN="
        
        for i, line in enumerate(lines):
            if line.strip().startswith(admin_token_prefix):
                lines[i] = f"{admin_token_prefix}{token}\n"
                admin_token_found = True
                break
        
        # 如果没找到管理员token配置，添加到文件末尾
        if not admin_token_found:
            # 查找用户配置部分
            user_config_section_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith("# 用户账户配置"):
                    user_config_section_found = True
                    # 在用户配置部分后面添加token
                    insert_index = i + 1
                    while insert_index < len(lines) and not lines[insert_index].strip().startswith("#"):
                        insert_index += 1
                    lines.insert(insert_index, f"{admin_token_prefix}{token}\n")
                    break
            
            # 如果没有找到用户配置部分，在文件末尾添加
            if not user_config_section_found:
                lines.append(f"\n# 用户账户配置\n")
                lines.append(f"# 格式: USER_TOKEN_用户名=JWT令牌\n")
                lines.append(f"{admin_token_prefix}{token}\n")
        
        # 写入更新后的配置
        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        console.print(f"[green]✓ 管理员token已保存到配置文件: {config_path}[/green]")
        console.print(f"[dim]下次启动时，将自动使用此token进行认证[/dim]")
        return True
        
    except Exception as e:
        console.print(f"[red]错误: 保存管理员token到配置文件失败 - {e}[/red]")
        return False


async def _verify_user_credentials(username: str, password: str) -> Optional[User]:
    """验证管理员凭据
    
    Args:
        username: 用户名（应为'admin'）
        password: 密码
        
    Returns:
        User: 验证成功的用户对象，如果验证失败则返回None
    """
    try:
        from sqlalchemy import select
        from src.codemcp.utils.password import verify_password
        
        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                console.print(f"[red]错误: 管理员 '{username}' 不存在[/red]")
                return None
            
            if not verify_password(password, user.hashed_password):
                console.print(f"[red]错误: 密码不正确[/red]")
                return None
            
            if not user.is_active:
                console.print(f"[red]错误: 管理员 '{username}' 已被禁用[/red]")
                return None
            
            if not user.is_superuser:
                console.print(f"[red]错误: 用户 '{username}' 不是管理员[/red]")
                return None
            
            return user
    except Exception as e:
        console.print(f"[red]错误: 验证管理员凭据失败 - {e}[/red]")
        return None


async def _change_password(user: User, current_password: str, new_password: str) -> bool:
    """修改管理员密码
    
    Args:
        user: 用户对象
        current_password: 当前密码
        new_password: 新密码
        
    Returns:
        bool: 密码修改是否成功
    """
    try:
        from src.codemcp.utils.password import verify_password, get_password_hash, is_password_strong
        
        # 验证当前密码
        if not verify_password(current_password, user.hashed_password):
            console.print(f"[red]错误: 当前密码不正确[/red]")
            return False
        
        # 检查新密码强度
        if not is_password_strong(new_password):
            console.print(f"[red]错误: 新密码强度不足[/red]")
            console.print(f"[dim]密码必须至少8个字符，包含数字和字母[/dim]")
            return False
        
        # 检查新密码是否与当前密码相同
        if verify_password(new_password, user.hashed_password):
            console.print(f"[red]错误: 新密码不能与当前密码相同[/red]")
            return False
        
        # 更新密码哈希
        new_hashed_password = get_password_hash(new_password)
        
        async with AsyncSessionFactory() as db:
            # 重新获取用户对象以确保在同一个会话中
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.id == user.id)
            )
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                console.print(f"[red]错误: 管理员不存在[/red]")
                return False
            
            db_user.hashed_password = new_hashed_password
            await db.commit()
            
            console.print(f"[green]✓ 密码修改成功![/green]")
            console.print(f"[dim]下次登录时请使用新密码[/dim]")
            return True
    except Exception as e:
        console.print(f"[red]错误: 修改密码失败 - {e}[/red]")
        return False


async def _prompt_change_password_if_default(user: User) -> bool:
    """如果管理员使用默认密码，提示修改密码
    
    Args:
        user: 用户对象
        
    Returns:
        bool: 是否成功修改密码（如果用户选择不修改，返回True）
    """
    from src.codemcp.config import settings
    from src.codemcp.utils.password import verify_password
    
    # 检查是否为默认密码
    default_password = settings.admin_password
    if verify_password(default_password, user.hashed_password):
        console.print(f"[bold red]🚨 严重安全警告: 您正在使用默认密码![/bold red]")
        console.print(f"[bold yellow]默认密码 'admin123' 极易被猜测，存在严重安全风险![/bold yellow]")
        console.print()
        console.print(f"[bold]为了系统安全，您必须立即修改密码![/bold]")
        console.print()
        
        # 显示安全建议
        console.print(f"[dim]安全建议:[/dim]")
        console.print(f"[dim]  • 使用至少12个字符的复杂密码[/dim]")
        console.print(f"[dim]  • 包含大小写字母、数字和特殊字符[/dim]")
        console.print(f"[dim]  • 避免使用常见单词或个人信息[/dim]")
        console.print()
        
        # 强制要求修改密码，不再提供跳过选项
        console.print(f"[bold green]强制密码修改[/bold green]")
        
        # 提示输入当前密码
        current_password = Prompt.ask(
            "当前密码",
            password=True,
            default=default_password
        )
        
        # 提示输入新密码
        new_password = Prompt.ask(
            "新密码",
            password=True
        )
        
        # 确认新密码
        confirm_password = Prompt.ask(
            "确认新密码",
            password=True
        )
        
        if new_password != confirm_password:
            console.print(f"[red]错误: 两次输入的密码不一致[/red]")
            return False
        
        # 检查新密码强度
        from src.codemcp.utils.password import is_password_strong
        if not is_password_strong(new_password):
            console.print(f"[red]错误: 新密码强度不足[/red]")
            console.print(f"[dim]密码必须至少8个字符，包含数字和字母[/dim]")
            console.print(f"[dim]建议使用更复杂的密码以提高安全性[/dim]")
            
            # 允许用户继续使用弱密码，但给出警告
            if not Confirm.ask("确定要使用这个弱密码吗？"):
                return False
        
        # 检查新密码是否与默认密码相同
        if verify_password(new_password, user.hashed_password):
            console.print(f"[red]错误: 新密码不能与当前默认密码相同[/red]")
            return False
        
        # 修改密码
        success = await _change_password(user, current_password, new_password)
        if success:
            console.print(f"[bold green]✅ 密码修改成功![/bold green]")
            console.print(f"[dim]请妥善保管您的新密码[/dim]")
            console.print(f"[dim]建议定期更换密码以提高安全性[/dim]")
            return True
        else:
            console.print(f"[red]❌ 密码修改失败，请稍后再试[/red]")
            return False
    else:
        # 不是默认密码，不需要修改
        return True


@app.command()
def login(
    username: str = typer.Option(
        "admin",
        "--username",
        "-u",
        help="管理员用户名（默认为'admin'）",
        show_default=True,
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        help="管理员密码",
    ),
    save: bool = typer.Option(
        True,
        "--save/--no-save",
        help="是否保存登录信息到配置文件",
        show_default=True,
    ),
):
    """管理员登录并保存会话
    
    系统只有一个管理员账户（admin），登录后会检查是否为默认密码，
    如果是默认密码会提示修改。
    """
    console.print(f"[bold green]管理员登录[/bold green]")
    
    # 检查用户名是否为admin
    if username != "admin":
        console.print(f"[yellow]警告: 系统只有一个管理员账户 'admin'，将使用 'admin' 登录[/yellow]")
        username = "admin"
    
    # 验证管理员凭据
    user = asyncio.run(_verify_user_credentials(username, password))
    if not user:
        console.print(f"[red]❌ 登录失败[/red]")
        return
    
    console.print(f"[green]✅ 登录成功![/green]")
    console.print(f"[dim]欢迎回来, {user.username}![/dim]")
    
    # 检查是否为默认密码，如果是则提示修改
    password_changed = asyncio.run(_prompt_change_password_if_default(user))
    if not password_changed:
        console.print(f"[yellow]⚠️  密码修改失败，请稍后重新登录并修改密码[/yellow]")
    
    # 生成JWT令牌
    token = create_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_superuser=user.is_superuser
    )
    
    console.print(f"[dim]认证令牌已生成[/dim]")
    console.print(f"[dim]令牌类型: Bearer[/dim]")
    console.print(f"[dim]令牌有效期: 24小时[/dim]")
    
    # 保存令牌到配置文件
    if save:
        success = _save_user_token_to_config(user, token)
        if success:
            console.print(f"[green]✓ 登录信息已保存到配置文件[/green]")
            console.print(f"[dim]下次启动时，将自动使用此令牌进行认证[/dim]")
        else:
            console.print(f"[yellow]⚠️  保存登录信息失败[/yellow]")
    
    # 显示管理员信息
    console.print(f"\n[bold]管理员信息:[/bold]")
    console.print(f"  • 用户名: {user.username}")
    if user.email:
        console.print(f"  • 邮箱: {user.email}")
    console.print(f"  • 角色: 管理员")
    console.print(f"  • 状态: {'活跃' if user.is_active else '禁用'}")
    console.print(f"  • 创建时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command()
def info():
    """显示当前管理员信息
    
    显示当前配置的管理员信息和认证状态。
    """
    console.print("[bold green]管理员信息[/bold green]")
    
    # 读取当前目录配置文件
    config_path = Path.cwd() / ".codemcp"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析配置
            import re
            token_match = re.search(r"USER_TOKEN_ADMIN=(\S+)", content)
            
            if token_match:
                admin_token = token_match.group(1)
                console.print(f"[green]✓ 管理员token已配置[/green]")
                console.print(f"[dim]token: {admin_token[:30]}...[/dim]")
                
                # 验证token
                from src.codemcp.utils.jwt import decode_token
                try:
                    payload = decode_token(admin_token)
                    console.print(f"[green]✓ token有效[/green]")
                    console.print(f"  • 用户名: {payload.get('username', '未知')}")
                    console.print(f"  • 用户ID: {payload.get('user_id', '未知')}")
                    console.print(f"  • 过期时间: {payload.get('exp', '未知')}")
                except Exception as e:
                    console.print(f"[red]✗ token无效或已过期: {e}[/red]")
            else:
                console.print(f"[yellow]⚠️  管理员token未配置[/yellow]")
                console.print(f"[dim]使用 'codemcp user login' 命令登录并保存token[/dim]")
                
        except Exception as e:
            console.print(f"[red]错误: 读取配置文件失败 - {e}[/red]")
    else:
        console.print("[dim]当前目录没有配置文件[/dim]")
        console.print("[dim]使用 'codemcp user login' 命令登录并生成配置文件[/dim]")


@app.command()
def change_password():
    """修改管理员密码
    
    修改当前管理员账户的密码。
    """
    console.print(f"[bold green]修改管理员密码[/bold green]")
    
    # 提示输入当前密码
    current_password = Prompt.ask(
        "当前密码",
        password=True
    )
    
    # 验证当前管理员
    user = asyncio.run(_verify_user_credentials("admin", current_password))
    if not user:
        console.print(f"[red]❌ 密码验证失败[/red]")
        return
    
    # 提示输入新密码
    new_password = Prompt.ask(
        "新密码",
        password=True
    )
    
    # 确认新密码
    confirm_password = Prompt.ask(
        "确认新密码",
        password=True
    )
    
    if new_password != confirm_password:
        console.print(f"[red]错误: 两次输入的密码不一致[/red]")
        return
    
    # 修改密码
    success = asyncio.run(_change_password(user, current_password, new_password))
    if success:
        console.print(f"[bold green]✅ 密码修改成功![/bold green]")
        console.print(f"[dim]下次登录时请使用新密码[/dim]")
    else:
        console.print(f"[red]❌ 密码修改失败[/red]")


if __name__ == "__main__":
    app()