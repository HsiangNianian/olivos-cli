# -*- coding: utf-8 -*-
"""
run 命令实现
"""

import subprocess
import sys
from pathlib import Path

from ...core import ConfigManager, get_logger

logger = get_logger()


def cmd_run(config_manager: ConfigManager, args) -> int:
    """直接运行 OlivOS"""
    config = config_manager.config
    install_path = config.git.expanded_install_path

    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        logger.info_print("请先运行: olivos-cli init")
        return 1

    main_py = install_path / "main.py"
    if not main_py.exists():
        logger.error_print(f"未找到 main.py: {main_py}")
        return 1

    logger.step(f"启动 OlivOS: {main_py}")

    # 构建 Python 命令
    cmd = [sys.executable, str(main_py)]

    # 添加环境变量
    env = {"PYTHONUNBUFFERED": "1"}
    if args.dev:
        env["OLIVOS_DEV"] = "1"
        logger.info_print("开发模式")
    if args.debug:
        env["OLIVOS_DEBUG"] = "1"
        logger.info_print("调试模式")

    import os

    for key, value in env.items():
        os.environ[key] = value

    # 运行
    result = subprocess.call(cmd, cwd=str(install_path))
    return result
