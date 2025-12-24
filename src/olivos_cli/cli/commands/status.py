# -*- coding: utf-8 -*-
"""
status 命令实现
"""

import subprocess
from pathlib import Path

from ...core import ConfigManager, get_logger
from ...systemd import SystemdManager

logger = get_logger()


def cmd_status(config_manager: ConfigManager, args) -> int:
    """状态监控"""
    config = config_manager.config
    install_path = config.git.expanded_install_path

    if args.watch:
        return _cmd_status_watch(config_manager)
    elif args.health:
        return _cmd_status_health(config_manager)
    else:
        return _cmd_status_show(config, install_path)


def _cmd_status_show(config, install_path: Path) -> int:
    """显示状态"""
    from rich.console import Console
    from rich.table import Table

    console = logger.console

    # OlivOS 目录状态
    table = Table(title="OlivOS 状态")
    table.add_column("项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("安装路径", str(install_path))
    table.add_row("目录存在", "[green]是[/green]" if install_path.exists() else "[red]否[/red]")

    if install_path.exists():
        from ...git import GitOperator

        git = GitOperator()
        git_status = git.get_repo_status(install_path)
        if git_status.get("exists"):
            table.add_row("当前分支", git_status.get("branch", "-"))
            table.add_row("当前提交", git_status.get("commit", "-")[:8])

    # systemd 服务状态
    systemd = SystemdManager(user_mode=config.systemd.user_mode)
    service_status = systemd.status(config.systemd.service_name)
    table.add_row("服务已加载", "[green]是[/green]" if service_status.get("loaded") else "[red]否[/red]")
    table.add_row("服务运行中", "[green]是[/green]" if service_status.get("running") else "[red]否[/red]")

    console.print(table)
    return 0


def _cmd_status_health(config_manager: ConfigManager) -> int:
    """健康检查"""
    logger.step("执行健康检查...")

    config = config_manager.config
    install_path = config.git.expanded_install_path

    checks = []

    # 检查目录
    checks.append(("OlivOS 目录", install_path.exists()))

    # 检查 git
    from ...git import GitOperator

    git = GitOperator()
    checks.append(("Git 可用", git.check_git()))

    # 检查配置
    checks.append(("配置文件存在", config_manager.config_path.exists()))

    # 检查包管理器
    from ...package import get_package_manager

    try:
        pkg_mgr = get_package_manager(
            name=config.package.manager,
            auto_install=False,
        )
        checks.append((f"{config.package.manager} 可用", pkg_mgr.is_available()))
    except Exception:
        checks.append((f"{config.package.manager} 可用", False))

    # 打印结果
    from rich.console import Console
    from rich.table import Table

    console = logger.console

    table = Table(title="健康检查结果")
    table.add_column("检查项", style="cyan")
    table.add_column("状态", style="green")

    all_passed = True
    for name, passed in checks:
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        table.add_row(name, status)
        if not passed:
            all_passed = False

    console.print(table)

    return 0 if all_passed else 1


def _cmd_status_watch(config_manager: ConfigManager) -> int:
    """实时监控"""
    # 使用 watch 命令定期刷新
    cmd = ["watch", "-n", "2", "olivos-cli", "status"]
    subprocess.call(cmd)
    return 0
