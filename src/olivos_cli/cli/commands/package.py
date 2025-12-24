# -*- coding: utf-8 -*-
"""
package 命令实现
"""

from pathlib import Path

from ...core import ConfigManager, get_logger
from ...core.exceptions import PackageError
from ...package import get_package_manager
from ...utils import check_requirements_compatibility, get_requirements_file

logger = get_logger()


def cmd_package(config_manager: ConfigManager, args) -> int:
    """包管理"""
    action = args.pkg_action

    if not action:
        # 显示帮助信息
        logger.info_print("用法: olivos-cli package [ACTION] [OPTIONS]")
        logger.info_print("")
        logger.info_print("动作:")
        logger.info_print("  install (i)   安装依赖")
        logger.info_print("  update (up)   更新依赖")
        logger.info_print("  list (ls)     列出已安装的包")
        logger.info_print("")
        logger.info_print("使用 'olivos-cli package [ACTION] --help' 查看具体动作的帮助")
        return 0

    config = config_manager.config
    install_path = config.git.expanded_install_path

    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        logger.info_print("请先运行: olivos-cli init")
        return 1

    pkg_mgr = get_package_manager(
        name=config.package.manager,
        auto_install=config.package.auto_install,
        index_url=config.package.uv.index_url,
    )

    if action == "install":
        return _cmd_package_install(pkg_mgr, install_path, args)
    elif action == "update":
        return _cmd_package_update(pkg_mgr, install_path)
    elif action == "list":
        return _cmd_package_list(pkg_mgr, install_path)

    return 0


def _cmd_package_install(pkg_mgr, install_path: Path, args) -> int:
    """安装依赖"""
    if args.packages:
        # 安装指定的包
        for package in args.packages:
            try:
                pkg_mgr.add(package, install_path)
            except PackageError as e:
                logger.error_print(str(e))
                return 1
    else:
        # 安装全部依赖 - 使用共享的 requirements 文件选择函数
        requirements_file = get_requirements_file(install_path)

        if requirements_file.exists():
            # 检查兼容性并显示警告
            warnings = check_requirements_compatibility(requirements_file)
            for warning in warnings:
                logger.warning_print(warning)

            try:
                pkg_mgr.install(install_path, requirements_file)
            except PackageError as e:
                logger.error_print(str(e))
                return 1
        else:
            logger.error_print("未找到依赖文件")
            return 1

    return 0


def _cmd_package_update(pkg_mgr, install_path: Path) -> int:
    """更新依赖"""
    try:
        pkg_mgr.update(install_path)
        return 0
    except PackageError as e:
        logger.error_print(str(e))
        return 1


def _cmd_package_list(pkg_mgr, install_path: Path) -> int:
    """列出已安装的包"""
    packages = pkg_mgr.list_installed(install_path)

    from rich.console import Console
    from rich.table import Table

    console = logger.console

    table = Table(title="已安装的包")
    table.add_column("包名", style="cyan")
    table.add_column("版本", style="green")

    for pkg in sorted(packages):
        table.add_row(pkg, "-")

    console.print(table)
    return 0
