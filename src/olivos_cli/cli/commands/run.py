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

    # 检查是否存在虚拟环境
    VENV_DIR = ".venv"
    venv_path = install_path / VENV_DIR
    if venv_path.exists():
        # Windows: venv_path / "Scripts" / "python.exe"
        # Linux/Mac: venv_path / "bin" / "python"
        if sys.platform == "win32":
            python_bin = venv_path / "Scripts" / "python.exe"
        else:
            python_bin = venv_path / "bin" / "python"

        if python_bin.exists():
            logger.info_print(f"使用虚拟环境 Python: {python_bin}")
            cmd = [str(python_bin), str(main_py)]
        else:
            logger.warning_print(f"虚拟环境 Python 不存在: {python_bin}")
            cmd = [sys.executable, str(main_py)]
    else:
        logger.info_print("未检测到虚拟环境，使用系统 Python")
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
