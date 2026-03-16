"""
CLI 配置管理

Console CLI 的配置管理和持久化。
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import settings as app_settings
from ..exceptions import ConfigurationError

# 默认配置文件路径
CONFIG_DIR = Path.home() / ".config" / "codemcp"
CONFIG_FILE = CONFIG_DIR / "cli_config.json"


class CLIConfig:
    """CLI 配置管理器"""

    def __init__(self, config_file: Optional[Path] = None):
        """初始化 CLI 配置

        Args:
            config_file: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_file = config_file or CONFIG_FILE
        self._config: Dict[str, Any] = {}
        self.load()

    @property
    def config_dir(self) -> Path:
        """配置目录"""
        return self.config_file.parent

    def ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                raise ConfigurationError(f"加载配置文件失败: {e}")
        else:
            # 使用默认配置
            self._config = self.get_default_config()
            self.save()

    def save(self) -> None:
        """保存配置文件"""
        self.ensure_config_dir()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise ConfigurationError(f"保存配置文件失败: {e}")

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "api": {
                "base_url": "http://localhost:8000",
                "timeout": 30,
                "api_prefix": app_settings.api_prefix,
            },
            "ui": {
                "theme": "default",
                "refresh_interval": 2.0,
                "show_timestamps": True,
                "compact_mode": False,
            },
            "monitor": {
                "follow": True,
                "auto_scroll": True,
                "highlight_errors": True,
                "show_system_stats": True,
            },
            "auth": {
                "token": None,
                "token_file": None,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点号分隔（如 "api.base_url"）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值

        Args:
            key: 配置键，支持点号分隔
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        # 遍历到最后一层
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value
        self.save()

    def delete(self, key: str) -> bool:
        """删除配置键

        Args:
            key: 配置键，支持点号分隔

        Returns:
            是否成功删除
        """
        keys = key.split(".")
        config = self._config

        # 遍历到倒数第二层
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                return False
            config = config[k]

        # 删除键
        if keys[-1] in config:
            del config[keys[-1]]
            self.save()
            return True

        return False

    def clear(self) -> None:
        """清空配置（恢复默认）"""
        self._config = self.get_default_config()
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()


# 全局配置实例
_config_instance: Optional[CLIConfig] = None


def get_config() -> CLIConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = CLIConfig()
    return _config_instance


def set_config(config: CLIConfig) -> None:
    """设置全局配置实例"""
    global _config_instance
    _config_instance = config