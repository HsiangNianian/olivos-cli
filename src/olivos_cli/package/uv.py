# -*- coding: utf-8 -*-
"""
UV 包管理器实现
"""

import shutil
import subprocess
from pathlib import Path

from ..core.exceptions import PackageError
from ..core.logger import get_logger
from ..utils import check_command, run_command, run_command_stream
from .base import PackageManager

logger = get_logger()


class UVPackageManager(PackageManager):
    """UV 包��理器"""

    name = "uv"

    def __init__(self, auto_install: bool = True, index_url: str = None, verbose: bool = False):
        self.auto_install = auto_install
        self.index_url = index_url
        self.verbose = verbose

    def is_available(self) -> bool:
        """检查 uv 是否可用"""
        return check_command("uv")

    def ensure_available(self) -> None:
        """确保 uv 可用"""
        if not self.is_available():
            if not self.auto_install:
                raise PackageError("uv 未安装，请运行: pip install uv")
            self._install_uv()

    def _install_uv(self) -> None:
        """安装 uv"""
        logger.step("正在安装 uv...")
        try:
            # 尝试使用 pip 安装
            result = subprocess.run(
                ["pip", "install", "uv"],
                capture=True,
                text=True,
            )
            if result.returncode != 0:
                # 尝试使用官方安装脚本
                result = subprocess.run(
                    ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"],
                    shell=True,
                )
                if result.returncode != 0:
                    raise PackageError("uv 安装失败")
            logger.success("uv 安装成功")
        except Exception as e:
            raise PackageError(f"uv 安装失败: {e}") from e

    def install(self, target_dir: Path, requirements: Path) -> bool:
        """安装依赖"""
        self.ensure_available()

        if not requirements.exists():
            raise PackageError(f"依赖文件不存在: {requirements}")

        cmd = ["uv", "pip", "install", "-r", str(requirements)]
        if self.index_url:
            cmd.extend(["--index-url", self.index_url])

        logger.step(f"正在安装依赖: {requirements.name}")

        if self.verbose:
            # 使用流式输出
            returncode = run_command_stream(
                cmd,
                cwd=str(target_dir),
                line_callback=lambda line: logger.verbose(line),
                error_callback=lambda line: logger.verbose(line),
            )
            if returncode != 0:
                raise PackageError(f"依赖安装失败，返回码: {returncode}")
        else:
            result = run_command(cmd, cwd=str(target_dir), check=False)
            if result.returncode != 0:
                raise PackageError(f"依赖安装失败: {result.stderr}")

        logger.success("依赖安装成功")
        return True

    def install_venv(self, target_dir: Path, venv_path: Path, requirements: Path) -> bool:
        """在虚拟环境中安装依赖

        Args:
            target_dir: 目标目录（OlivOS 根目录）
            venv_path: 虚拟环境路径
            requirements: 依赖文件路径
        """
        self.ensure_available()

        if not requirements.exists():
            raise PackageError(f"依赖文件不存在: {requirements}")

        if not venv_path.exists():
            raise PackageError(f"虚拟环境不存在: {venv_path}")

        # 使用 --python 参数指定虚拟环境的 Python
        import sys

        if sys.platform == "win32":
            python_bin = venv_path / "Scripts" / "python.exe"
        else:
            python_bin = venv_path / "bin" / "python"

        if not python_bin.exists():
            raise PackageError(f"虚拟环境 Python 不存在: {python_bin}")

        cmd = ["uv", "pip", "install", "-r", str(requirements), "--python", str(python_bin)]
        if self.index_url:
            cmd.extend(["--index-url", self.index_url])

        logger.step(f"正在虚拟环境安装依赖: {requirements.name}")

        if self.verbose:
            # 使用流式输出
            returncode = run_command_stream(
                cmd,
                cwd=str(target_dir),
                line_callback=lambda line: logger.verbose(line),
                error_callback=lambda line: logger.verbose(line),
            )
            if returncode != 0:
                raise PackageError(f"依赖安装失败，返回码: {returncode}")
        else:
            result = run_command(cmd, cwd=str(target_dir), check=False)
            if result.returncode != 0:
                raise PackageError(f"依赖安装失败: {result.stderr}")

        logger.success("依赖安装成功")
        return True

    def add(self, package: str, target_dir: Path) -> bool:
        """添加包"""
        self.ensure_available()

        cmd = ["uv", "pip", "install", package]
        if self.index_url:
            cmd.extend(["--index-url", self.index_url])

        logger.step(f"正在添加包: {package}")
        result = run_command(cmd, cwd=str(target_dir), check=False)

        if result.returncode != 0:
            raise PackageError(f"包添加失败: {result.stderr}")

        logger.success(f"已添加: {package}")
        return True

    def remove(self, package: str, target_dir: Path) -> bool:
        """移除包"""
        self.ensure_available()

        cmd = ["uv", "pip", "uninstall", "-y", package]

        logger.step(f"正在移除包: {package}")
        result = run_command(cmd, cwd=str(target_dir), check=False)

        if result.returncode != 0:
            raise PackageError(f"包移除失败: {result.stderr}")

        logger.success(f"已移除: {package}")
        return True

    def update(self, target_dir: Path) -> bool:
        """更新依赖"""
        self.ensure_available()

        cmd = ["uv", "pip", "sync", "--upgrade"]
        if self.index_url:
            cmd.extend(["--index-url", self.index_url])

        logger.step("正在更新依赖...")
        result = run_command(cmd, cwd=str(target_dir), check=False)

        if result.returncode != 0:
            # uv sync 可能会失败，尝试逐个更新
            cmd = ["uv", "pip", "install", "--upgrade"]
            if self.index_url:
                cmd.extend(["--index-url", self.index_url])
            result = run_command(cmd, cwd=str(target_dir), check=False)

        logger.success("依赖更新成功")
        return True

    def list_installed(self, target_dir: Path) -> list[str]:
        """列出已安装的包"""
        self.ensure_available()

        cmd = ["uv", "pip", "list", "--format=json"]
        result = run_command(cmd, cwd=str(target_dir), capture=True)

        if result.returncode != 0:
            return []

        try:
            import json

            packages = json.loads(result.stdout)
            return [p["name"] for p in packages]
        except Exception:
            return []
