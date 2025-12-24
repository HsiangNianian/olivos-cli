# -*- coding: utf-8 -*-
"""
包管理器基类
"""

from abc import ABC, abstractmethod
from pathlib import Path


class PackageManager(ABC):
    """包管理器基类"""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """检查包管理器是否可用"""
        pass

    @abstractmethod
    def install(self, target_dir: Path, requirements: Path) -> bool:
        """安装依赖"""
        pass

    @abstractmethod
    def install_venv(self, target_dir: Path, venv_path: Path, requirements: Path) -> bool:
        """在虚拟环境中安装依赖

        Args:
            target_dir: 目标目录（OlivOS 根目录）
            venv_path: 虚拟环境路径
            requirements: 依赖文件路径
        """
        pass

    @abstractmethod
    def add(self, package: str, target_dir: Path) -> bool:
        """添加包"""
        pass

    @abstractmethod
    def remove(self, package: str, target_dir: Path) -> bool:
        """移除包"""
        pass

    @abstractmethod
    def update(self, target_dir: Path) -> bool:
        """更新依赖"""
        pass

    @abstractmethod
    def list_installed(self, target_dir: Path) -> list[str]:
        """列出已安装的包"""
        pass
