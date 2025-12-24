# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import shutil
import subprocess
import sys
from typing import Optional, Callable


def run_command(
    cmd: list[str],
    cwd: Optional[str] = None,
    capture: bool = True,
    check: bool = False,
    env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """运行 shell 命令

    Args:
        cmd: 命令列表
        cwd: 工作目录
        capture: 是否捕获输出
        check: 是否检查返回码
        env: 环境变量

    Returns:
        subprocess.CompletedProcess
    """
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        check=check,
        env=env,
    )


def run_command_stream(
    cmd: list[str],
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    line_callback: Optional[Callable[[str], None]] = None,
    error_callback: Optional[Callable[[str], None]] = None,
) -> int:
    """运行命令并实时输出日志

    Args:
        cmd: 命令列表
        cwd: 工作目录
        env: 环境变量
        line_callback: 每行输出时的回调函数
        error_callback: 每行错误输出时的回调函数

    Returns:
        返回码
    """
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # 行缓冲
        env=env,
    )

    import threading

    returncode = [0]  # 使用列表以便在闭包中修改

    def read_stdout():
        for line in process.stdout:
            line = line.rstrip('\n\r')
            if line_callback:
                line_callback(line)
            elif line.strip():
                print(f"  {line}")

    def read_stderr():
        nonlocal returncode
        for line in process.stderr:
            line = line.rstrip('\n\r')
            if error_callback:
                error_callback(line)
            elif line.strip():
                print(f"  {line}", file=sys.stderr)

    # 启动线程读取输出
    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)

    stdout_thread.start()
    stderr_thread.start()

    # 等待进程结束
    returncode[0] = process.wait()

    # 等待输出线程结束
    stdout_thread.join(timeout=1)
    stderr_thread.join(timeout=1)

    return returncode[0]


def find_command(name: str) -> Optional[str]:
    """查找系统中的命令

    Args:
        name: 命令名称

    Returns:
        命令完整路径或 None
    """
    return shutil.which(name)


def check_command(name: str) -> bool:
    """检查命令是否存在

    Args:
        name: 命令名称

    Returns:
        是否存在
    """
    return find_command(name) is not None


def get_editor() -> str:
    """获取系统默认编辑器"""
    import os

    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    for candidate in ["vim", "vi", "nano", "micro"]:
        if check_command(candidate):
            return candidate

    return "vi"


from .requirements import (
    check_requirements_compatibility,
    get_requirements_file,
    get_requirements_info,
)

__all__ = [
    "run_command",
    "run_command_stream",
    "find_command",
    "check_command",
    "get_editor",
    "get_requirements_file",
    "get_requirements_info",
    "check_requirements_compatibility",
]
