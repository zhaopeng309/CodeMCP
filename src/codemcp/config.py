"""
CodeMCP 配置管理

基于 pydantic-settings 的环境变量配置。
支持项目级 .env 文件，优先级顺序：
1. 当前工作目录的 .env 文件
2. CODEMCP_HOME 环境变量指定的目录中的 .env 文件
3. 默认的 .env 文件（当前目录）
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_files() -> List[str]:
    """查找环境配置文件，按优先级顺序返回
    
    优先级顺序（后读取的覆盖先读取的）：
    1. CODEMCP_HOME 环境变量指定的目录中的 .codemcp 文件（安装目录）
    2. 当前工作目录的 .codemcp 文件
    
    注意：CODEMCP_HOME 需要用户自己保证设置，这是安装目录
    
    Returns:
        环境文件路径列表，按读取顺序排列
    """
    env_files = []
    
    # 1. CODEMCP_HOME 环境变量指定的目录中的 .codemcp 文件（安装目录）
    codemcp_home = os.environ.get("CODEMCP_HOME")
    if codemcp_home:
        home_env = Path(codemcp_home) / ".codemcp"
        if home_env.exists():
            env_files.append(str(home_env))
    
    # 2. 当前工作目录的 .codemcp 文件
    current_dir = Path.cwd()
    current_env = current_dir / ".codemcp"
    if current_env.exists():
        env_files.append(str(current_env))
    
    # 3. 如果没有找到任何 .codemcp 文件，至少包含当前目录的 .codemcp（即使不存在）
    # 这样 pydantic-settings 会使用默认值
    if not env_files:
        env_files.append(".codemcp")
    
    return env_files


def ensure_project_config() -> Path:
    """确保项目级配置文件存在
    
    如果当前目录没有 .codemcp 文件，自动从安装目录（CODEMCP_HOME）拷贝一个到当前目录。
    这是 CLI 工具启动时应该调用的函数。
    
    Returns:
        项目级配置文件路径
    """
    current_dir = Path.cwd()
    project_config = current_dir / ".codemcp"
    
    # 如果项目级配置文件已存在，直接返回
    if project_config.exists():
        return project_config
    
    # 获取安装目录
    codemcp_home = os.environ.get("CODEMCP_HOME")
    if not codemcp_home:
        # 如果没有设置 CODEMCP_HOME，尝试使用默认位置
        # 假设当前工作目录就是安装目录
        codemcp_home = str(current_dir)
    
    # 检查安装目录是否有配置文件
    home_config = Path(codemcp_home) / ".codemcp"
    if home_config.exists():
        # 拷贝配置文件到当前目录
        import shutil
        shutil.copy2(home_config, project_config)
        print(f"已从安装目录拷贝配置文件到: {project_config}")
    else:
        # 如果安装目录也没有配置文件，创建一个空的配置文件
        with open(project_config, "w", encoding="utf-8") as f:
            f.write("# CodeMCP 项目级配置文件\n")
            f.write("# 此文件用于覆盖安装目录的全局配置\n")
            f.write("# 优先级：当前目录 > 安装目录\n\n")
            f.write("# 认证配置\n")
            f.write("# AUTH_ENABLED=true\n")
            f.write("# SECRET_KEY=your-secret-key-here\n")
            f.write("# JWT_ALGORITHM=HS256\n\n")
            f.write("# 服务器配置\n")
            f.write("# HOST=0.0.0.0\n")
            f.write("# PORT=8000\n")
            f.write("# DATABASE_URL=sqlite:///./codemcp.db\n")
        print(f"已创建项目级配置文件: {project_config}")
    
    return project_config


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """自定义配置源，动态设置 env_file"""
        # 动态查找环境文件
        env_files = find_env_files()
        
        # 创建新的 dotenv_settings 源，使用动态找到的文件
        from pydantic_settings.sources import DotEnvSettingsSource
        dotenv_settings = DotEnvSettingsSource(
            settings_cls=settings_cls,
            env_file=env_files,
            env_file_encoding="utf-8",
            case_sensitive=False,
        )
        
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./codemcp.db",
        description="数据库连接 URL",
        examples=["sqlite:///./codemcp.db", "postgresql://user:password@localhost/codemcp"],
    )

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, description="服务器监听端口", ge=1, le=65535)
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # API 配置
    api_prefix: str = Field(default="/api/v1", description="API 前缀")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS 允许的来源",
    )

    # 任务执行配置
    task_window_size: int = Field(default=5, description="任务窗口大小", ge=1, le=100)
    max_retries: int = Field(default=3, description="最大重试次数", ge=0, le=10)
    default_priority: int = Field(default=0, description="默认优先级")

    # 日志配置
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    log_format: str = Field(default="json", description="日志格式", pattern="^(json|text)$")

    # 认证配置
    auth_enabled: bool = Field(
        default=True,
        description="是否启用认证。如果禁用，所有 API 都不需要认证；如果启用，需要 JWT 令牌"
    )
    
    # JWT 认证配置（当 auth_enabled=True 时生效）
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="JWT 签名密钥，至少8个字符",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT 算法",
        pattern="^(HS256|HS384|HS512|RS256|RS384|RS512|ES256|ES384|ES512)$",
    )

    # 初始管理员账户（可选，当 auth_enabled=True 时生效）
    admin_username: str = Field(default="admin", description="初始管理员用户名")
    admin_password: str = Field(default="admin123", description="初始管理员密码")
    admin_email: str = Field(default="admin@example.com", description="初始管理员邮箱")

    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """解析 CORS_ORIGINS 环境变量"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()


if __name__ == "__main__":
    # 测试配置加载
    print(settings.model_dump_json(indent=2))