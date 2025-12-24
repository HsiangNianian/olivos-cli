# -*- coding: utf-8 -*-
"""
update 命令实现
"""

from ...core import VERSION, get_logger

logger = get_logger()


def cmd_update(config_manager, args) -> int:
    """更新 OlivOS-CLI 自身"""
    logger.step(f"当前版本: {VERSION}")
    logger.info_print("更新功能待实现")
    logger.info_print("请使用: pip install --upgrade olivos-cli")
    return 0
