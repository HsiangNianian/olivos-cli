"""
包管理模块
"""

from .base import PackageManager
from .pdm import PDMPackageManager
from .pip import PipPackageManager
from .uv import UVPackageManager

# 包管理器 Map
PACKAGE_MANAGERS_MAP = {
    "uv": UVPackageManager,
    "pip": PipPackageManager,
    "pdm": PDMPackageManager,
}


def get_package_manager(
    name: str,
    auto_install: bool = True,
    index_url: str = None,
    verbose: bool = False,
) -> PackageManager:
    """获取包管理器实例

    Args:
        name: 包管理器名称
        auto_install: 是否自动安装包管理器
        index_url: 镜像源地址
        verbose: 是否显示详细输出

    Returns:
        包管理器实例
    """
    if name not in PACKAGE_MANAGERS_MAP:
        from ..core.exceptions import PackageError

        raise PackageError(f"包管理器在当前环境无效: {name}")

    manager_class = PACKAGE_MANAGERS_MAP[name]

    if name == "uv":
        return manager_class(auto_install=auto_install, index_url=index_url, verbose=verbose)
    elif name == "pdm":
        return manager_class(auto_install=auto_install, index_url=index_url, verbose=verbose)
    else:
        return manager_class(index_url=index_url, verbose=verbose)


__all__ = [
    "PackageManager",
    "UVPackageManager",
    "PipPackageManager",
    "PDMPackageManager",
    "get_package_manager",
]
