# -*- coding: utf-8 -*-
"""
config 命令实现
"""

import subprocess
from pathlib import Path

from ...core import ConfigManager, get_logger
from ...utils import get_editor

logger = get_logger()


def cmd_config(config_manager: ConfigManager, args) -> int:
    """配置管理"""
    action = args.cfg_action

    if not action:
        # 显示帮助信息
        logger.info_print("用法: olivos-cli config [ACTION] [OPTIONS]")
        logger.info_print("")
        logger.info_print("动作:")
        logger.info_print("  show      显示配置")
        logger.info_print("  get       获取配置项")
        logger.info_print("  set       设置配置项")
        logger.info_print("  unset     删除配置项")
        logger.info_print("  edit      编辑配置文件")
        logger.info_print("  reset     重置为默认配置")
        logger.info_print("")
        logger.info_print("使用 'olivos-cli config [ACTION] --help' 查看具体动作的帮助")
        return 0

    if action == "show":
        return _cmd_config_show(config_manager)
    elif action == "get":
        return _cmd_config_get(config_manager, args)
    elif action == "set":
        return _cmd_config_set(config_manager, args)
    elif action == "unset":
        return _cmd_config_unset(config_manager, args)
    elif action == "edit":
        return _cmd_config_edit(config_manager)
    elif action == "reset":
        return _cmd_config_reset(config_manager)

    return 0


def _cmd_config_show(config_manager: ConfigManager) -> int:
    """显示配置"""
    from dataclasses import asdict

    config = config_manager.config
    data = asdict(config)

    import json
    from rich.console import Console
    from rich.syntax import Syntax

    console = logger.console
    toml_str = json.dumps(data, indent=2, ensure_ascii=False)

    syntax = Syntax(toml_str, "json", theme="monokai", line_numbers=True)
    console.print(syntax)

    return 0


def _cmd_config_get(config_manager: ConfigManager, args) -> int:
    """获取配置项"""
    value = config_manager.get(args.key)

    if value is None:
        logger.error_print(f"配置项不存在: {args.key}")
        return 1

    logger.console.print(f"{args.key} = {value}")
    return 0


def _cmd_config_set(config_manager: ConfigManager, args) -> int:
    """设置配置项"""
    try:
        config_manager.set(args.key, args.value)
        config_manager.save()
        logger.success(f"配置已更新: {args.key} = {args.value}")
        return 0
    except Exception as e:
        logger.error_print(f"设置失败: {e}")
        return 1


def _cmd_config_unset(config_manager: ConfigManager, args) -> int:
    """删除配置项"""
    logger.info_print(f"unset 功能待实现: {args.key}")
    return 0


def _cmd_config_edit(config_manager: ConfigManager) -> int:
    """编辑配置文件"""
    config_path = config_manager.config_path

    # 确保配置文件存在
    if not config_path.exists():
        config_manager.init_default_config()

    editor = get_editor()
    logger.step(f"使用 {editor} 编辑配置...")

    result = subprocess.call([editor, str(config_path)])
    return result


def _cmd_config_reset(config_manager: ConfigManager) -> int:
    """重置为默认配置"""
    from ...utils.prompt import confirm

    if not confirm("确定要重置为默认配置吗？这将覆盖现有配置。"):
        return 0

    config_manager.reset()
    config_manager.save()
    logger.success("配置已重置为默认值")
    return 0
