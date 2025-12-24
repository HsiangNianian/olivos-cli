# -*- coding: utf-8 -*-
"""
adapter 命令实现
"""

from pathlib import Path

from ...core import SUPPORTED_ADAPTERS, ConfigManager, get_logger
from ...olivos import OlivOSConfigManager
from ...utils.prompt import confirm

logger = get_logger()


def cmd_adapter(config_manager: ConfigManager, args) -> int:
    """适配器管理"""
    action = args.adapt_action

    if not action:
        # 显示帮助信息
        logger.info_print("用法: olivos-cli adapter [ACTION] [OPTIONS]")
        logger.info_print("")
        logger.info_print("动作:")
        logger.info_print("  list (ls)    列出支持的适配器")
        logger.info_print("  enable       启用适配器（添加账号）")
        logger.info_print("  disable      禁用适配器（删除该类型的所有账号）")
        logger.info_print("  config (cfg) 配置适配器")
        logger.info_print("")
        logger.info_print("使用 'olivos-cli adapter [ACTION] --help' 查看具体动作的帮助")
        return 0

    config = config_manager.config
    install_path = config.git.expanded_install_path

    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        logger.info_print("请先运行: olivos-cli init")
        return 1

    olivos_config = OlivOSConfigManager(install_path)

    if action == "list":
        return _cmd_adapter_list(olivos_config)
    elif action == "enable":
        return _cmd_adapter_enable(olivos_config, args.name)
    elif action == "disable":
        return _cmd_adapter_disable(olivos_config, args.name)
    elif action == "config":
        return _cmd_adapter_config(olivos_config, args)

    return 0


def _cmd_adapter_list(config: OlivOSConfigManager) -> int:
    """列出支持的适配器及其状态"""
    from rich.console import Console
    from rich.table import Table

    console = logger.console

    table = Table(title="支持的适配器")
    table.add_column("类型", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("描述", style="yellow")
    table.add_column("账号数", style="blue")

    for key, info in SUPPORTED_ADAPTERS.items():
        count = config.count_accounts_by_adapter(key)
        status = "[green]已启用[/green]" if count > 0 else "[dim]未启用[/dim]"
        table.add_row(key, info["name"], info["description"], f"{count} {status}")

    console.print(table)
    return 0


def _cmd_adapter_enable(config: OlivOSConfigManager, name: str) -> int:
    """启用适配器"""
    if name not in SUPPORTED_ADAPTERS:
        logger.error_print(f"不支持的适配器: {name}")
        logger.info_print(f"支持的适配器: {', '.join(SUPPORTED_ADAPTERS.keys())}")
        return 1

    info = SUPPORTED_ADAPTERS[name]
    logger.info_print(f"适配器 {info['name']} ({name})")
    logger.info_print("")
    logger.info_print("适配器通过添加账号来启用。请使用以下命令添加账号：")
    logger.info_print(f"  olivos-cli account add --adapter {name}")
    logger.info_print("")
    logger.info_print("或者使用交互模式：")
    logger.info_print(f"  olivos-cli account add")

    # 显示当前已有的账号
    count = config.count_accounts_by_adapter(name)
    if count > 0:
        accounts = config.list_accounts_by_adapter(name)
        logger.info_print("")
        logger.info_print(f"当前该适配器已有 {count} 个账号：")
        for acc in accounts:
            logger.info_print(f"  - {acc.id}")

    return 0


def _cmd_adapter_disable(config: OlivOSConfigManager, name: str) -> int:
    """禁用适配器（删除该类型的所有账号）"""
    if name not in SUPPORTED_ADAPTERS:
        logger.error_print(f"不支持的适配器: {name}")
        logger.info_print(f"支持的适配器: {', '.join(SUPPORTED_ADAPTERS.keys())}")
        return 1

    count = config.count_accounts_by_adapter(name)
    if count == 0:
        logger.info_print(f"适配器 {name} 没有配置的账号")
        return 0

    info = SUPPORTED_ADAPTERS[name]
    logger.warning_print(f"即将删除 {info['name']} ({name}) 的所有 {count} 个账号")

    if not confirm(f"确定要禁用适配器 {name} 并删除其所有账号吗？"):
        logger.info_print("操作已取消")
        return 0

    removed = config.remove_accounts_by_adapter(name)
    if removed > 0:
        logger.success(f"已删除 {removed} 个账号，适配器 {name} 已禁用")
    else:
        logger.warning_print("没有删除任何账号")

    return 0


def _cmd_adapter_config(config: OlivOSConfigManager, args) -> int:
    """配置适配器"""
    name = args.name

    if name not in SUPPORTED_ADAPTERS:
        logger.error_print(f"不支持的适配器: {name}")
        logger.info_print(f"支持的适配器: {', '.join(SUPPORTED_ADAPTERS.keys())}")
        return 1

    info = SUPPORTED_ADAPTERS[name]

    if args.get:
        return _cmd_adapter_config_get(config, name, args.get)
    elif args.set:
        return _cmd_adapter_config_set(config, name, args.set)
    else:
        # 显示适配器信息
        from rich.console import Console
        from rich.table import Table

        console = logger.console

        table = Table(title=f"适配器: {info['name']} ({name})")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("SDK 类型", info["sdk_type"])
        table.add_row("平台类型", info["platform_type"])
        table.add_row("描述", info["description"])

        count = config.count_accounts_by_adapter(name)
        table.add_row("账号数量", str(count))

        console.print(table)

        if count > 0:
            accounts = config.list_accounts_by_adapter(name)
            logger.info_print("")
            logger.info_print("账号列表：")
            for acc in accounts:
                logger.info_print(f"  - ID: {acc.id}")

        return 0


def _cmd_adapter_config_get(config: OlivOSConfigManager, name: str, key: str) -> int:
    """获取适配器配置"""
    if name not in SUPPORTED_ADAPTERS:
        logger.error_print(f"不支持的适配器: {name}")
        return 1

    info = SUPPORTED_ADAPTERS[name]

    # 显示支持的可配置项
    valid_keys = {
        "sdk_type": info["sdk_type"],
        "platform_type": info["platform_type"],
        "name": info["name"],
        "description": info["description"],
    }

    if key in valid_keys:
        logger.info_print(f"{name}.{key} = {valid_keys[key]}")
        return 0
    else:
        logger.error_print(f"未知的配置项: {key}")
        logger.info_print(f"可用的配置项: {', '.join(valid_keys.keys())}")
        return 1


def _cmd_adapter_config_set(config: OlivOSConfigManager, name: str, value: str) -> int:
    """设置适配器配置"""
    logger.error_print("适配器配置暂不支持直接设置")
    logger.info_print("适配器通过账号配置。请使用：")
    logger.info_print(f"  olivos-cli account add --adapter {name}")
    return 1
