# -*- coding: utf-8 -*-
"""
核心模块
"""

from importlib.metadata import version

from .config import Config, ConfigManager, expand_path, path_to_str
from .const import (
    ADAPTER_TYPE_CHOICES,
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
    SUPPORTED_ADAPTERS,
    SYSTEMD_USER_DIR,
)
from .exceptions import (
    AccountError,
    AdapterError,
    ConfigError,
    FileNotFoundError as OlivOSFileNotFoundError,
    GitError,
    OlivOSCLIError,
    OlivOSConfigError,
    PackageError,
    ProcessError,
    SystemdError,
    ValidationError,
)
from .logger import OlivOSLogger, get_logger


def get_version() -> str:
    """动态获取包版本"""
    try:
        return version("olivos-cli")
    except Exception:
        return "0.0.0"


VERSION = get_version()

__all__ = [
    # config
    "Config",
    "ConfigManager",
    "expand_path",
    "path_to_str",
    # const
    "ADAPTER_TYPE_CHOICES",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "DATA_DIR",
    "DEFAULT_BRANCH",
    "DEFAULT_MIRROR_URL",
    "DEFAULT_REPO_URL",
    "DEFAULT_SERVICE_NAME",
    "LOG_DIR",
    "LOG_LEVELS",
    "PACKAGE_MANAGERS",
    "SUPPORTED_ADAPTERS",
    "SYSTEMD_USER_DIR",
    "VERSION",
    # exceptions
    "AccountError",
    "AdapterError",
    "ConfigError",
    "OlivOSFileNotFoundError",
    "GitError",
    "OlivOSCLIError",
    "OlivOSConfigError",
    "PackageError",
    "ProcessError",
    "SystemdError",
    "ValidationError",
    # logger
    "OlivOSLogger",
    "get_logger",
    # adapters
    "ADAPTER_GROUPS",
    "ALL_ADAPTERS",
    "get_adapter_by_platform_sdk",
    "get_adapter_config",
    "list_adapter_configs",
    # validation
    "validate_account_config",
    "validate_extends",
    "get_adapter_required_fields",
    "get_adapter_optional_fields",
    "get_adapter_model_type_options",
    "get_adapter_extends_options",
]


# Lazy imports for larger modules
def __getattr__(name: str):
    if name == "ADAPTER_GROUPS":
        from .adapters import ADAPTER_GROUPS
        return ADAPTER_GROUPS
    elif name == "ALL_ADAPTERS":
        from .adapters import ALL_ADAPTERS
        return ALL_ADAPTERS
    elif name == "get_adapter_config":
        from .adapters import get_adapter_config
        return get_adapter_config
    elif name == "list_adapter_configs":
        from .adapters import list_adapter_configs
        return list_adapter_configs
    elif name == "validate_account_config":
        from .validation import validate_account_config
        return validate_account_config
    elif name == "validate_extends":
        from .validation import validate_extends
        return validate_extends
    elif name == "get_adapter_required_fields":
        from .validation import get_adapter_required_fields
        return get_adapter_required_fields
    elif name == "get_adapter_optional_fields":
        from .validation import get_adapter_optional_fields
        return get_adapter_optional_fields
    elif name == "get_adapter_model_type_options":
        from .validation import get_adapter_model_type_options
        return get_adapter_model_type_options
    elif name == "get_adapter_extends_options":
        from .validation import get_adapter_extends_options
        return get_adapter_extends_options
    elif name == "get_adapter_by_platform_sdk":
        from .adapters import get_adapter_by_platform_sdk
        return get_adapter_by_platform_sdk
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
