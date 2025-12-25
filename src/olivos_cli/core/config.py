# -*- coding: utf-8 -*-
"""
配置管理模块
处理 TOML 配置文件读写
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
except ImportError:
    tomli_w = None

from .const import (
    CACHE_DIR,
    CONFIG_DIR,
    CONFIG_FILE,
    DATA_DIR,
    DEFAULT_BRANCH,
    DEFAULT_MIRROR_URL,
    DEFAULT_REPO_URL,
    DEFAULT_SERVICE_NAME,
    LOG_DIR,
    LOG_LEVELS,
    PACKAGE_MANAGERS,
    SYSTEMD_USER_DIR,
)
from .exceptions import ConfigError
from .logger import get_logger

logger = get_logger()


def expand_path(path: str) -> Path:
    """扩展路径中的 ~ 和环境变量"""
    expanded = os.path.expanduser(path)
    expanded = os.path.expandvars(expanded)
    return Path(expanded)


def path_to_str(path: Path) -> str:
    """将 Path 转换为字符串，尽可能使用 ~ 缩写"""
    home = Path.home()
    try:
        if path.is_relative_to(home):
            return "~/" + str(path.relative_to(home))
    except (TypeError, AttributeError):
        pass
    return str(path)


@dataclass
class CLIConfig:
    """CLI 配置"""

    verbose: bool = False
    quiet: bool = False
    yes: bool = False
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    def __post_init__(self):
        if self.log_file is not None:
            self.log_file = expand_path(str(self.log_file))


@dataclass
class GitConfig:
    """Git 配置"""

    repo_url: str = DEFAULT_REPO_URL
    mirror_url: str = DEFAULT_MIRROR_URL
    use_mirror: bool = False
    install_path: str = "./OlivOS"
    branch: str = DEFAULT_BRANCH
    commit_hash: Optional[str] = None
    depth: int = 1
    auto_pull: bool = True

    @property
    def expanded_install_path(self) -> Path:
        return expand_path(self.install_path).resolve()

    @property
    def effective_url(self) -> str:
        return self.mirror_url if self.use_mirror else self.repo_url


@dataclass
class PackageUVConfig:
    """UV 包管理器配置"""

    python_version: str = "3.11"
    cache_dir: str = "~/.cache/olivos-cli/uv"
    index_url: str = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
    extra_index_url: list[str] = field(default_factory=list)

    @property
    def expanded_cache_dir(self) -> Path:
        return expand_path(self.cache_dir).resolve()


@dataclass
class PackageConfig:
    """包管理器配置"""

    manager: str = "pip"
    auto_install: bool = True
    uv: PackageUVConfig = field(default_factory=PackageUVConfig)

    def __post_init__(self):
        if self.manager not in PACKAGE_MANAGERS:
            raise ConfigError(f"包管理器在当前环境无效: {self.manager}")
        if isinstance(self.uv, dict):
            self.uv = PackageUVConfig(**self.uv)


@dataclass
class SystemdRuntimeConfig:
    """systemd 运行时配置"""

    working_directory: Optional[str] = None
    python_path: str = "python3"
    main_script: str = "main.py"
    environment: dict[str, str] = field(default_factory=lambda: {"PYTHONUNBUFFERED": "1"})
    restart_policy: str = "on-failure"
    restart_sec: int = 10

    def __post_init__(self):
        if self.working_directory is None:
            self.working_directory = "./OlivOS"


@dataclass
class SystemdConfig:
    """systemd 配置"""

    user_mode: bool = True
    service_dir: str = "~/.config/systemd/user"
    service_name: str = DEFAULT_SERVICE_NAME
    runtime: SystemdRuntimeConfig = field(default_factory=SystemdRuntimeConfig)

    @property
    def expanded_service_dir(self) -> Path:
        return expand_path(self.service_dir).resolve()

    def __post_init__(self):
        if isinstance(self.runtime, dict):
            self.runtime = SystemdRuntimeConfig(**self.runtime)


@dataclass
class OlivOSBasicConfig:
    """OlivOS 基本配置"""

    system_name: str = "OlivOS"
    debug_mode: bool = False
    plugin_auto_restart: bool = True


@dataclass
class OlivOSConfig:
    """OlivOS 配置"""

    root_path: str = "./OlivOS"
    conf_path: str = "./OlivOS/conf"
    plugin_path: str = "./OlivOS/plugin"
    log_path: str = "~/.local/state/olivos"
    basic: OlivOSBasicConfig = field(default_factory=OlivOSBasicConfig)

    @property
    def expanded_root_path(self) -> Path:
        return expand_path(self.root_path).resolve()

    @property
    def expanded_conf_path(self) -> Path:
        return expand_path(self.conf_path).resolve()

    @property
    def expanded_plugin_path(self) -> Path:
        return expand_path(self.plugin_path).resolve()

    @property
    def expanded_log_path(self) -> Path:
        return expand_path(self.log_path).resolve()

    def __post_init__(self):
        if isinstance(self.basic, dict):
            self.basic = OlivOSBasicConfig(**self.basic)


@dataclass
class LoggingConfig:
    """日志配置"""

    olivos_log_file: str = "~/.local/state/olivos/olivos.log"
    log_rotation: bool = True
    max_size_mb: int = 100
    keep_days: int = 30

    @property
    def expanded_log_file(self) -> Path:
        return expand_path(self.olivos_log_file).resolve()


@dataclass
class MonitoringConfig:
    """监控配置"""

    health_check_interval: int = 60
    health_check_endpoint: Optional[str] = None


@dataclass
class PluginsConfig:
    """插件配置"""

    plugin_dirs: list[str] = field(
        default_factory=lambda: ["./OlivOS/plugin", "./plugins"]
    )
    auto_load: list[str] = field(default_factory=list)

    @property
    def expanded_plugin_dirs(self) -> list[Path]:
        return [expand_path(p).resolve() for p in self.plugin_dirs]


@dataclass
class InstanceConfig:
    """实例配置"""

    name: str = "primary"
    path: str = "./OlivOS"
    service_name: str = DEFAULT_SERVICE_NAME
    enabled: bool = True
    branch: str = DEFAULT_BRANCH

    @property
    def expanded_path(self) -> Path:
        return expand_path(self.path).resolve()


@dataclass
class AdvancedConfig:
    """高级配置"""

    update_strategy: str = "auto"
    backup_before_update: bool = True
    backup_dir: str = "~/.local/share/olivos-cli/backups"
    concurrent_downloads: int = 4

    @property
    def expanded_backup_dir(self) -> Path:
        return expand_path(self.backup_dir).resolve()


@dataclass
class Config:
    """OlivOS-CLI 总配置"""

    cli: CLIConfig = field(default_factory=CLIConfig)
    git: GitConfig = field(default_factory=GitConfig)
    package: PackageConfig = field(default_factory=PackageConfig)
    systemd: SystemdConfig = field(default_factory=SystemdConfig)
    olivos: OlivOSConfig = field(default_factory=OlivOSConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    plugins: PluginsConfig = field(default_factory=PluginsConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)
    instances: list[InstanceConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """从字典创建配置对象"""
        config = cls()

        if "cli" in data:
            config.cli = CLIConfig(**_filter_keys(CLIConfig, data["cli"]))
        if "git" in data:
            config.git = GitConfig(**_filter_keys(GitConfig, data["git"]))
        if "package" in data:
            config.package = PackageConfig(**_filter_keys(PackageConfig, data["package"]))
        if "systemd" in data:
            config.systemd = SystemdConfig(**_filter_keys(SystemdConfig, data["systemd"]))
        if "olivos" in data:
            config.olivos = OlivOSConfig(**_filter_keys(OlivOSConfig, data["olivos"]))
        if "logging" in data:
            config.logging = LoggingConfig(**_filter_keys(LoggingConfig, data["logging"]))
        if "monitoring" in data:
            config.monitoring = MonitoringConfig(**_filter_keys(MonitoringConfig, data["monitoring"]))
        if "plugins" in data:
            config.plugins = PluginsConfig(**_filter_keys(PluginsConfig, data["plugins"]))
        if "advanced" in data:
            config.advanced = AdvancedConfig(**_filter_keys(AdvancedConfig, data["advanced"]))
        if "instances" in data:
            config.instances = [InstanceConfig(**_filter_keys(InstanceConfig, i)) for i in data["instances"]]

        return config

    def to_dict(self) -> dict[str, Any]:
        """转换为字典，过滤掉 None 值"""
        from dataclasses import asdict

        def filter_none(obj):
            """递归过滤掉 None 值"""
            if isinstance(obj, dict):
                return {k: filter_none(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [filter_none(item) for item in obj if item is not None]
            return obj

        return filter_none(asdict(self))

    def validate(self) -> list[str]:
        """验证配置，返回错误列表"""
        errors = []

        if self.cli.log_level not in LOG_LEVELS:
            errors.append(f"无效的日志级别: {self.cli.log_level}")

        if self.git.depth < 0:
            errors.append("git.depth 不能为负数")

        if self.package.manager not in PACKAGE_MANAGERS:
            errors.append(f"包管理器在当前环境无效: {self.package.manager}")

        if self.advanced.concurrent_downloads < 1:
            errors.append("concurrent_downloads 至少为 1")

        return errors


def _filter_keys(dataclass_cls: type, data: dict[str, Any]) -> dict[str, Any]:
    """过滤字典，只保留 dataclass 中定义的字段"""
    import dataclasses
    # 获取 dataclass 的所有字段名
    field_names = {f.name for f in dataclasses.fields(dataclass_cls)}
    # 只保留有效的字段
    return {k: v for k, v in data.items() if k in field_names}


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self._config: Optional[Config] = None

    @property
    def config(self) -> Config:
        """获取配置，如果未加载则先加载"""
        if self._config is None:
            self.load()
        return self._config

    def load(self, force: bool = False) -> Config:
        """加载配置文件"""
        if self._config is not None and not force:
            return self._config

        if not self.config_path.exists():
            logger.debug(f"配置文件不存在: {self.config_path}")
            self._config = Config()
            return self._config

        if tomllib is None:
            raise ConfigError(
                "缺少 TOML 解析库。\n"
                f"当前 Python 版本: {sys.version_info.major}.{sys.version_info.minor}\n"
                "请安装 tomli: pip install tomli tomli-w"
            )

        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
            self._config = Config.from_dict(data)
            logger.debug(f"配置已加载: {self.config_path}")
        except Exception as e:
            raise ConfigError(f"加载配置文件失败: {e}") from e

        return self._config

    def save(self, config: Optional[Config] = None) -> None:
        """保存配置文件"""
        config = config or self._config
        if config is None:
            raise ConfigError("没有可保存的配置")

        # 检查 TOML 写入库是否可用
        if tomli_w is None:
            raise ConfigError(
                "缺少 TOML 写入库。\n"
                f"当前 Python 版本: {sys.version_info.major}.{sys.version_info.minor}\n"
                "请安装: pip install tomli-w"
            )

        # 验证配置
        errors = config.validate()
        if errors:
            raise ConfigError("配置验证失败:\n" + "\n".join(errors))

        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = config.to_dict()

            with open(self.config_path, "wb") as f:
                tomli_w.dump(data, f)

            logger.info(f"配置已保存: {self.config_path}")
        except Exception as e:
            raise ConfigError(f"保存配置文件失败: {e}") from e

    def _dict_to_toml(self, data: dict, indent: int = 0) -> str:
        """字典转 TOML (回退方案)"""
        lines = []
        prefix = " " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}[{key}]")
                lines.append(self._dict_to_toml(value, indent))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key} = []")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key} = {str(value).lower()}")
            elif isinstance(value, str):
                lines.append(f'{prefix}{key} = "{value}"')
            elif isinstance(value, (int, float)):
                lines.append(f"{prefix}{key} = {value}")
            elif value is None:
                continue

        return "\n".join(lines)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split(".")
        config = self._config or self.config

        obj = config
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            else:
                raise ConfigError(f"无效的配置键: {key}")

        if not hasattr(obj, keys[-1]):
            raise ConfigError(f"无效的配置键: {key}")

        setattr(obj, keys[-1], value)

    def reset(self) -> Config:
        """重置为默认配置"""
        self._config = Config()
        return self._config

    def init_default_config(self) -> None:
        """初始化默认配置文件"""
        self._config = Config()
        self.save()
        logger.success(f"默认配置已创建: {self.config_path}")

    def ensure_dirs(self) -> None:
        """确保所有必要目录存在"""
        dirs = [
            CONFIG_DIR,
            DATA_DIR,
            CACHE_DIR,
            LOG_DIR,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
