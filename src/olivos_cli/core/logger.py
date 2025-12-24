"""
日志模块
基于 rich 的日志输出
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from .const import LOG_DIR, LOG_LEVELS


class OlivOSLogger:
    """OlivOS-CLI 日志管理器"""

    _instance: Optional["OlivOSLogger"] = None
    _logger: Optional[logging.Logger] = None
    _console: Optional[Console] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is not None:
            return
        self._console = Console()
        self._logger = logging.getLogger("olivos-cli")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self.__init__()
        return self._logger

    @property
    def console(self) -> Console:
        if self._console is None:
            self.__init__()
        return self._console

    def setup(
        self,
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
        verbose: bool = False,
        quiet: bool = False,
    ):
        """设置日志处理器

        Args:
            log_level: 日志级别
            log_file: 日志文件路径
            verbose: 详细输出模式
            quiet: 静默模式
        """
        # 清除现有处理器
        self.logger.handlers.clear()

        if quiet:
            log_level = "ERROR"
        elif verbose:
            log_level = "DEBUG"

        level = getattr(logging, log_level.upper(), logging.INFO)

        # 控制台处理器 (使用 RichHandler)
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
        )
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(name)s | %(message)s",
            datefmt="[%Y-%m-%d %H:%M:%S]",
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)

    def success(self, msg: str):
        """输出成功消息"""
        self.console.print(f"[bold green]S:[/bold green] {msg}")

    def info_print(self, msg: str):
        """输出信息消息"""
        self.console.print(f"[cyan]I:[/cyan] {msg}")

    def warning_print(self, msg: str):
        """输出警告消息"""
        self.console.print(f"[bold yellow]W:[/bold yellow] {msg}")

    def error_print(self, msg: str):
        """输出错误消息"""
        # 使用 Text 避免解析消息中的方括号
        from rich.text import Text

        text = Text()
        text.append("C: ", style="bold red")
        text.append(str(msg))
        self.console.print(text)

    def step(self, msg: str):
        """输出步骤消息"""
        from rich.text import Text

        text = Text()
        text.append("> ", style="bold blue")
        text.append(str(msg))
        self.console.print(text)

    def verbose(self, msg: str, indent: int = 2):
        """输出详细日志（灰色缩进）"""
        from rich.text import Text

        text = Text()
        prefix = "  " * indent
        text.append(prefix, style="dim")
        text.append(str(msg), style="dim")
        self.console.print(text)

    def raw_output(self, msg: str):
        """输出原始内容（不添加前缀）"""
        from rich.text import Text

        text = Text()
        text.append(str(msg), style="dim")
        self.console.print(text)


get_logger = OlivOSLogger
