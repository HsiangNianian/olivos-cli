# -*- coding: utf-8 -*-
"""
service 命令实现
"""

import subprocess
import sys
from pathlib import Path

from ...core import ConfigManager, get_logger
from ...core.exceptions import SystemdError
from ...systemd import SystemdManager

logger = get_logger()


def cmd_service(config_manager: ConfigManager, args) -> int:
    """服务管理"""
    action = args.svc_action

    if not action:
        # 显示帮助信息
        logger.info_print("用法: olivos-cli service [ACTION] [OPTIONS]")
        logger.info_print("")
        logger.info_print("动作:")
        logger.info_print("  install      安装 systemd 服务")
        logger.info_print("  uninstall    卸载服务")
        logger.info_print("  enable       启用开机自启")
        logger.info_print("  disable      禁用开机自启")
        logger.info_print("  start        启动服务")
        logger.info_print("  stop         停止服务")
        logger.info_print("  restart (r)  重启服务")
        logger.info_print("  status (st)  查看服务状态")
        logger.info_print("  logs (log)   查看服务日志")
        logger.info_print("")
        logger.info_print("使用 'olivos-cli service [ACTION] --help' 查看具体动作的帮助")
        return 0

    config = config_manager.config
    install_path = config.git.expanded_install_path
    service_name = config.systemd.service_name

    systemd = SystemdManager(
        user_mode=config.systemd.user_mode,
        service_dir=config.systemd.expanded_service_dir,
    )

    if action == "install":
        return _cmd_service_install(systemd, config_manager, install_path)
    elif action == "uninstall":
        return _cmd_service_uninstall(systemd, service_name)
    elif action == "enable":
        return _cmd_service_enable(systemd, service_name)
    elif action == "disable":
        return _cmd_service_disable(systemd, service_name)
    elif action == "start":
        return _cmd_service_start(systemd, service_name)
    elif action == "stop":
        return _cmd_service_stop(systemd, service_name)
    elif action == "restart":
        return _cmd_service_restart(systemd, service_name)
    elif action == "status":
        return _cmd_service_status(systemd, service_name)
    elif action == "logs":
        return _cmd_service_logs(systemd, service_name, args, install_path)

    return 0


def _cmd_service_install(systemd: SystemdManager, config_manager: ConfigManager, install_path: Path) -> int:
    """安装服务"""
    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        logger.info_print("请先运行: olivos-cli init")
        return 1

    try:
        systemd.install_service(
            name="olivos",
            working_directory=install_path,
            config=config_manager,
        )
        logger.success("服务已安装")
        logger.info_print("使用以下命令管理服务:")
        logger.info_print(f"  启用: olivos-cli service enable")
        logger.info_print(f"  启动: olivos-cli service start")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_uninstall(systemd: SystemdManager, service_name: str) -> int:
    """卸载服务"""
    try:
        systemd.uninstall_service(service_name)
        logger.success(f"服务已卸载: {service_name}")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_enable(systemd: SystemdManager, service_name: str) -> int:
    """启用开机自启"""
    try:
        systemd.enable(service_name)
        logger.success(f"服务已启用开机自启: {service_name}")
        logger.info_print("使用 'olivos-cli service start' 启动服务")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_disable(systemd: SystemdManager, service_name: str) -> int:
    """禁用开机自启"""
    try:
        systemd.disable(service_name)
        logger.success(f"服务已禁用开机自启: {service_name}")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_start(systemd: SystemdManager, service_name: str) -> int:
    """启动服务"""
    try:
        systemd.start(service_name)
        logger.success(f"服务已启动: {service_name}")
        logger.info_print("使用 'olivos-cli service status' 查看状态")
        logger.info_print("使用 'olivos-cli service logs' 查看日志")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_stop(systemd: SystemdManager, service_name: str) -> int:
    """停止服务"""
    try:
        systemd.stop(service_name)
        logger.success(f"服务已停止: {service_name}")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_restart(systemd: SystemdManager, service_name: str) -> int:
    """重启服务"""
    try:
        systemd.restart(service_name)
        logger.success(f"服务已重启: {service_name}")
        logger.info_print("使用 'olivos-cli service status' 查看状态")
        return 0
    except SystemdError as e:
        logger.error_print(str(e))
        return 1


def _cmd_service_status(systemd: SystemdManager, service_name: str) -> int:
    """查看服务状态"""
    status = systemd.status(service_name)

    from rich.console import Console
    from rich.table import Table

    console = logger.console

    table = Table(title=f"服务状态: {service_name}")
    table.add_column("项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("已加载", "[green]是[/green]" if status["loaded"] else "[red]否[/red]")
    table.add_row("已启用", "[green]是[/green]" if status["enabled"] else "[red]否[/red]")
    table.add_row("运行中", "[green]是[/green]" if status["running"] else "[red]否[/red]")
    table.add_row("PID", str(status["pid"]) if status["pid"] else "-")

    console.print(table)
    return 0


def _cmd_service_logs(systemd: SystemdManager, service_name: str, args, install_path: Path = None) -> int:
    """查看服务日志

    默认查看 OlivOS 应用日志，使用 --systemd 查看 systemd 日志
    """
    # 检查使用哪个日志源
    use_systemd = getattr(args, 'systemd', False)

    if not use_systemd:
        # 查看 OlivOS 应用日志（默认）
        if install_path is None:
            from ...core.config import expand_path
            install_path = expand_path("~/.local/share/olivos/OlivOS").resolve()

        log_file = install_path.parent / "logs" / "olivos.log"

        if not log_file.exists():
            logger.error_print(f"日志文件不存在: {log_file}")
            return 1

        # 读取日志文件
        result = subprocess.run(
            ["tail", "-n", str(args.lines), str(log_file)],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().split("\n")

        # 应用模式过滤和高亮
        pattern = getattr(args, 'pattern', None)
        if pattern:
            import re
            filtered_lines = [line for line in lines if re.search(pattern, line, re.IGNORECASE)]
            if filtered_lines:
                from rich.console import Console
                from rich.text import Text

                console = Console()
                for line in filtered_lines:
                    text = Text()
                    last_end = 0
                    for match in re.finditer(f"({re.escape(pattern)})", line, re.IGNORECASE):
                        text.append(line[last_end:match.start()])
                        text.append(match.group(), style="bold red")
                        last_end = match.end()
                    text.append(line[last_end:])
                    console.print(text)
            else:
                logger.info_print(f"未找到匹配 '{pattern}' 的日志")
        else:
            for line in lines:
                print(line)

        return 0

    # 使用 journalctl 查看 systemd 日志
    cmd = ["journalctl", "--user", "-u", f"{service_name}.service", "-n", str(args.lines)]

    if args.follow:
        cmd.append("-f")
        subprocess.call(cmd)
    else:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    return 0
