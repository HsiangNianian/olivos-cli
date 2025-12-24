# -*- coding: utf-8 -*-
"""
systemd 服务管理
"""

import os
import sys
from pathlib import Path
from typing import Optional

from ..core.config import ConfigManager, expand_path
from ..core.exceptions import SystemdError
from ..core.logger import get_logger
from ..utils import run_command
from .template import ServiceTemplateData, generate_service_file

logger = get_logger()

# 虚拟环境目录名
VENV_DIR = ".venv"


class SystemdManager:
    """systemd 服务管理器"""

    def __init__(self, user_mode: bool = True, service_dir: Optional[Path] = None):
        self.user_mode = user_mode
        self.service_dir = service_dir or expand_path("~/.config/systemd/user")

    def _get_systemctl_cmd(self) -> list[str]:
        """获取 systemctl 命令"""
        cmd = ["systemctl"]
        if self.user_mode:
            cmd.append("--user")
        return cmd

    def _run_systemctl(self, args: list[str], check: bool = False) -> bool:
        """运行 systemctl 命令"""
        cmd = self._get_systemctl_cmd() + args
        result = run_command(cmd, check=check)
        return result.returncode == 0

    def _detect_venv_python(self, working_directory: Path) -> Optional[str]:
        """检测虚拟环境中的 Python 路径

        Args:
            working_directory: OlivOS 工作目录

        Returns:
            虚拟环境 Python 路径，如果不存在则返回 None
        """
        venv_path = working_directory / VENV_DIR
        if not venv_path.exists():
            return None

        if sys.platform == "win32":
            python_bin = venv_path / "Scripts" / "python.exe"
        else:
            python_bin = venv_path / "bin" / "python"

        if python_bin.exists():
            return str(python_bin)
        return None

    def install_service(
        self,
        name: str,
        working_directory: Path,
        config: Optional[ConfigManager] = None,
    ) -> Path:
        """安装服务

        Args:
            name: 服务名称
            working_directory: 工作目录
            config: 配置管理器

        Returns:
            service 文件路径
        """
        # 检测虚拟环境
        venv_python = self._detect_venv_python(working_directory)
        if venv_python:
            logger.info_print(f"使用虚拟环境 Python: {venv_python}")
            python_executable = venv_python
        else:
            logger.info_print("未检测到虚拟环境，使用系统 Python")
            python_executable = sys.executable

        if config:
            cfg = config.config
            service_name = cfg.systemd.service_name
            template_data = ServiceTemplateData(
                instance_name=name,
                working_directory=str(working_directory),
                python_executable=python_executable,
                environment=cfg.systemd.runtime.environment,
                restart_policy=cfg.systemd.runtime.restart_policy,
                restart_sec=cfg.systemd.runtime.restart_sec,
            )
        else:
            service_name = "olivos-cli"
            template_data = ServiceTemplateData(
                instance_name=name,
                working_directory=str(working_directory),
                python_executable=python_executable,
            )

        # 生成 service 文件
        service_filename = f"{service_name}.service"
        service_path = self.service_dir / service_filename

        content = render_service_template(template_data)
        service_path.parent.mkdir(parents=True, exist_ok=True)
        service_path.write_text(content, encoding="utf-8")

        # 创建日志目录
        log_dir = Path(template_data.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        Path(template_data.log_file).touch(exist_ok=True)
        Path(template_data.error_log_file).touch(exist_ok=True)

        # 重载 systemd
        self._run_systemctl(["daemon-reload"])

        logger.success(f"服务已安装: {service_path}")
        return service_path

    def uninstall_service(self, name: str) -> bool:
        """卸载服务"""
        service_filename = f"{name}.service"
        service_path = self.service_dir / service_filename

        # 先停止并禁用
        self.stop(name)
        self.disable(name)

        # 删除文件
        if service_path.exists():
            service_path.unlink()
            self._run_systemctl(["daemon-reload"])
            logger.success(f"服务已卸载: {name}")
            return True

        return False

    def enable(self, name: str) -> bool:
        """启用开机自启"""
        service_filename = f"{name}.service"
        result = self._run_systemctl(["enable", service_filename])
        if result:
            logger.success(f"服务已启用: {name}")
        return result

    def disable(self, name: str) -> bool:
        """禁用开机自启"""
        service_filename = f"{name}.service"
        result = self._run_systemctl(["disable", service_filename])
        if result:
            logger.success(f"服务已禁用: {name}")
        return result

    def start(self, name: str) -> bool:
        """启动服务"""
        service_filename = f"{name}.service"
        result = self._run_systemctl(["start", service_filename])
        if result:
            logger.success(f"服务已启动: {name}")
        return result

    def stop(self, name: str) -> bool:
        """停止服务"""
        service_filename = f"{name}.service"
        result = self._run_systemctl(["stop", service_filename])
        if result:
            logger.success(f"服务已停止: {name}")
        return result

    def restart(self, name: str) -> bool:
        """重启服务"""
        service_filename = f"{name}.service"
        result = self._run_systemctl(["restart", service_filename])
        if result:
            logger.success(f"服务已重启: {name}")
        return result

    def status(self, name: str) -> dict:
        """获取服务状态"""
        service_filename = f"{name}.service"
        cmd = self._get_systemctl_cmd() + [
            "show",
            service_filename,
            "--property=LoadState,ActiveState,SubState,MainPID",
        ]
        result = run_command(cmd, capture=True)

        if result.returncode != 0:
            return {"loaded": False, "active": False, "running": False}

        status = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                status[key] = value

        loaded = status.get("LoadState", "not-found") == "loaded"
        active = status.get("ActiveState", "inactive") == "active"
        running = status.get("SubState", "dead") == "running"
        pid = int(status.get("MainPID", 0)) if status.get("MainPID", "0") != "0" else None

        return {
            "loaded": loaded,
            "active": active,
            "running": running,
            "enabled": self._is_enabled(name),
            "pid": pid,
        }

    def _is_enabled(self, name: str) -> bool:
        """检查服务是否已启用"""
        service_filename = f"{name}.service"
        cmd = self._get_systemctl_cmd() + [
            "is-enabled",
            service_filename,
        ]
        result = run_command(cmd, capture=True)
        return result.returncode == 0

    def logs(
        self,
        name: str,
        lines: int = 100,
        follow: bool = False,
    ) -> str:
        """获取服务日志"""
        service_filename = f"{name}.service"
        cmd = self._get_systemctl_cmd() + ["journalctl", "-u", service_filename]

        if follow:
            cmd.append("-f")
        else:
            cmd.extend(["-n", str(lines)])

        result = run_command(cmd, capture=False)
        return ""

    def get_service_path(self, name: str) -> Path:
        """获取 service 文件路径"""
        return self.service_dir / f"{name}.service"


# 导入 render_service_template 函数
from .template import render_service_template

__all__ = [
    "SystemdManager",
    "generate_service_file",
    "ServiceTemplateData",
    "render_service_template",
]
