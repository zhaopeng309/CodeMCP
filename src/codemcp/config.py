"""
CodeMCP 配置管理

基于 pydantic-settings 的环境变量配置。
"""

import json
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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