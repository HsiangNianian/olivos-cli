# -*- coding: utf-8 -*-
"""
logs 命令实现
"""

import re
import subprocess
from pathlib import Path

from ...core import ConfigManager, get_logger

logger = get_logger()


def cmd_logs(config_manager: ConfigManager, args) -> int:
    """日志查看

    默认显示 OlivOS 应用日志，使用 --cli 查看 CLI 工具日志
    """
    if args.cli:
        # 查看 CLI 日志
        config = config_manager.config
        log_file = config.logging.expanded_log_file
    else:
        # 查看 OlivOS 应用日志（默认）
        install_path = config_manager.config.git.expanded_install_path
        log_file = install_path.parent / "logs" / "olivos.log"

    if not log_file.exists():
        if args.cli:
            logger.info_print("CLI 工具日志文件不存在")
            logger.info_print("提示: 执行 olivos-cli 操作后会自动创建日志")
            # 尝试创建日志目录
            log_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            logger.error_print(f"日志文件不存在: {log_file}")
            logger.info_print("提示: 确保 OlivOS 服务已启动")
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
    elif args.follow:
        # 实时跟踪模式
        cmd = ["tail", "-f", str(log_file)]
        subprocess.call(cmd)
    else:
        # 普通显示
        for line in lines:
            print(line)

    return 0
