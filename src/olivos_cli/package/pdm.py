# -*- coding: utf-8 -*-
"""
PDM 包管理器实现
"""

import subprocess
import sys
from collections import deque
from pathlib import Path

from ..core.exceptions import PackageError
from ..core.logger import get_logger
from ..utils import run_command, run_command_stream
from .base import PackageManager

logger = get_logger()

# 显示的最大行数
MAX_OUTPUT_LINES = 4


class PDMPackageManager(PackageManager):
    """PDM 包管理器"""

    name = "pdm"
    VENV_DIR = ".venv"

    def __init__(self, auto_install: bool = True, index_url: str = None, verbose: bool = False):
        self.auto_install = auto_install
        self.index_url = index_url
        self.verbose = verbose

    def is_available(self) -> bool:
        """检查 PDM 是否可用"""
        try:
            result = run_command(["pdm", "--version"], capture=True, check=False)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def ensure_available(self) -> None:
        """确保 PDM 可用"""
        if not self.is_available():
            if self.auto_install:
                logger.step("正在安装 PDM...")
                # 使用 pip 安装 PDM
                install_cmd = [sys.executable, "-m", "pip", "install", "-U", "pdm"]
                result = run_command(install_cmd, check=False)
                if result.returncode != 0:
                    raise PackageError("PDM 安装失败")
                logger.success("PDM 安装成功")
            else:
                raise PackageError("PDM 不可用，请使用以下命令安装: pip install pdm")

    def _detect_venv_python(self, target_dir: Path) -> Path:
        """检测目标目录的虚拟环境 Python"""
        venv_path = target_dir / self.VENV_DIR
        if not venv_path.exists():
            return None

        if sys.platform == "win32":
            python_bin = venv_path / "Scripts" / "python.exe"
        else:
            python_bin = venv_path / "bin" / "python"

        return python_bin if python_bin.exists() else None

    def _get_pdm_command(self, target_dir: Path = None) -> list[str]:
        """获取 pdm 命令"""
        cmd = ["pdm"]

        # 如果有虚拟环境，设置 PDM_PYTHON 环境变量
        if target_dir:
            venv_python = self._detect_venv_python(target_dir)
            if venv_python:
                # 使用虚拟环境的 Python
                return cmd

        return cmd

    def _run_with_limited_output(self, cmd: list[str], cwd: str) -> int:
        """运行命令，只显示最后几行输出

        Args:
            cmd: 命令列表
            cwd: 工作目录

        Returns:
            返回码
        """
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # 使用 deque 保存最后几行
        output_buffer = deque(maxlen=MAX_OUTPUT_LINES)

        for line in process.stdout:
            line = line.strip()
            if line:
                output_buffer.append(line)

        returncode = process.wait()

        # 打印最后几行
        for output_line in output_buffer:
            logger.info_print(f"  {output_line}")

        return returncode

    def _run_with_scrolling_output(self, cmd: list[str], cwd: str) -> int:
        """运行命令，实时滚动显示最后几行输出

        Args:
            cmd: 命令列表
            cwd: 工作目录

        Returns:
            返回码
        """
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # 使用 deque 保存最后几行
        output_buffer = deque(maxlen=MAX_OUTPUT_LINES)
        line_count = 0

        for line in process.stdout:
            line = line.strip()
            if line:
                output_buffer.append(line)
                line_count += 1

                # 每次输出时清除并重新打印最后几行
                sys.stdout.write("\r\033[K")  # 清除当前行
                # 向上移动到第一个输出的位置
                if len(output_buffer) > 0:
                    sys.stdout.write(f"\033[{len(output_buffer)}F")
                # 重新打印所有缓冲的行
                for buffered_line in output_buffer:
                    sys.stdout.write("\r\033[K")  # 清除行
                    sys.stdout.write(f"  {buffered_line}\n")
                sys.stdout.flush()

        returncode = process.wait()
        print()  # 换行

        return returncode

    def install(self, target_dir: Path, requirements: Path) -> bool:
        """安装依赖"""
        self.ensure_available()

        if not requirements.exists():
            raise PackageError(f"依赖文件不存在: {requirements}")

        cmd = self._get_pdm_command(target_dir) + ["install", "-v"]
        # PDM index_url 通过环境变量设置

        logger.step(f"正在安装依赖: {requirements.name}")

        # 设置 PYPIPROXY_REWRITE 环境变量以支持镜像
        import os
        env = os.environ.copy()
        if self.index_url:
            env["PDM_INDEX_URL"] = self.index_url

        if self.verbose:
            returncode = self._run_with_scrolling_output(cmd, cwd=str(target_dir))
            if returncode != 0:
                raise PackageError(f"依赖安装失败，返回码: {returncode}")
        else:
            result = run_command(cmd, cwd=str(target_dir), check=False, env=env)
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

        # 获取虚拟环境的 Python 路径
        if sys.platform == "win32":
            python_bin = venv_path / "Scripts" / "python.exe"
        else:
            python_bin = venv_path / "bin" / "python"

        if not python_bin.exists():
            raise PackageError(f"虚拟环境 Python 不存在: {python_bin}")

        # 配置 PDM 使用虚拟环境的 Python
        logger.step(f"配置 PDM 使用虚拟环境: {venv_path}")
        use_cmd = ["pdm", "use", "-f", str(python_bin)]
        result = run_command(use_cmd, cwd=str(target_dir), check=False)
        if result.returncode != 0:
            logger.warning_print(f"PDM Python 配置警告: {result.stderr}")

        # 安装依赖
        cmd = ["pdm", "install", "-v"]

        logger.step(f"正在虚拟环境安装依赖: {requirements.name}")

        import os
        env = os.environ.copy()
        if self.index_url:
            env["PDM_INDEX_URL"] = self.index_url

        if self.verbose:
            returncode = self._run_with_scrolling_output(cmd, cwd=str(target_dir))
            if returncode != 0:
                raise PackageError(f"依赖安装失败，返回码: {returncode}")
        else:
            result = run_command(cmd, cwd=str(target_dir), check=False, env=env)
            if result.returncode != 0:
                raise PackageError(f"依赖安装失败: {result.stderr}")

        logger.success("依赖安装成功")
        return True

    def add(self, package: str, target_dir: Path) -> bool:
        """添加包"""
        self.ensure_available()

        cmd = self._get_pdm_command(target_dir) + ["add", package]
        # PDM index_url 在 config 中设置

        logger.step(f"正在添加包: {package}")
        result = run_command(cmd, cwd=str(target_dir), check=False)

        if result.returncode != 0:
            raise PackageError(f"包添加失败: {result.stderr}")

        logger.success(f"已添加: {package}")
        return True

    def remove(self, package: str, target_dir: Path) -> bool:
        """移除包"""
        self.ensure_available()

        cmd = self._get_pdm_command(target_dir) + ["remove", package]

        logger.step(f"正在移除包: {package}")
        result = run_command(cmd, cwd=str(target_dir), check=False)

        if result.returncode != 0:
            raise PackageError(f"包移除失败: {result.stderr}")

        logger.success(f"已移除: {package}")
        return True

    def update(self, target_dir: Path) -> bool:
        """更新依赖"""
        self.ensure_available()

        cmd = self._get_pdm_command(target_dir) + ["update"]

        logger.step("正在更新依赖...")
        result = run_command(cmd, cwd=str(target_dir), check=False)

        if result.returncode != 0:
            raise PackageError(f"依赖更新失败: {result.stderr}")

        logger.success("依赖更新成功")
        return True

    def list_installed(self, target_dir: Path) -> list[str]:
        """列出已安装的包"""
        self.ensure_available()

        cmd = self._get_pdm_command(target_dir) + ["list", "--format", "json"]
        result = run_command(cmd, cwd=str(target_dir), capture=True)

        if result.returncode != 0:
            return []

        try:
            import json

            packages = json.loads(result.stdout)
            return [p["name"] for p in packages]
        except Exception:
            return []
