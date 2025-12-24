# -*- coding: utf-8 -*-
"""
Requirements 文件选择工具
"""

import platform
import re
import sys
from pathlib import Path

# Pillow 最低版本要求（用于 Python 3.12+）
PILLOW_MIN_VERSION_PY312 = "10.0.0"


def get_requirements_file(install_path: Path) -> Path:
    """获取合适的 requirements 文件

    优先级：
    1. 根据系统和 Python 版本选择
    2. 回退到通用 requirements.txt

    Args:
        install_path: OlivOS 安装路径

    Returns:
        requirements 文件路径
    """
    python_version = sys.version_info
    system = platform.system()

    # 根据系统和 Python 版本选择
    if system == "Windows":
        if python_version >= (3, 12):
            # Python 3.12+ 需要 requirements312
            candidates = [
                install_path / "requirements312_win.txt",
                install_path / "requirements312.txt",
                install_path / "requirements310_win.txt",
                install_path / "requirements.txt",
            ]
        else:
            candidates = [
                install_path / "requirements310_win.txt",
                install_path / "requirements.txt",
            ]
    else:
        if python_version >= (3, 12):
            # Python 3.12+ 需要 requirements312
            candidates = [
                install_path / "requirements312.txt",
                install_path / "requirements310.txt",
                install_path / "requirements.txt",
            ]
        else:
            candidates = [
                install_path / "requirements310.txt",
                install_path / "requirements.txt",
            ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # 如果都不存在，返回默认
    return install_path / "requirements.txt"


def check_requirements_compatibility(requirements_file: Path) -> list[str]:
    """检查 requirements 文件与当前 Python 版本的兼容性

    Args:
        requirements_file: requirements 文件路径

    Returns:
        警告信息列表
    """
    warnings = []
    python_version = sys.version_info

    if not requirements_file.exists():
        return warnings

    # 只检查 Python 3.12+ 的 Pillow 兼容性
    if python_version >= (3, 12):
        try:
            with open(requirements_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找 Pillow 版本要求
            pillow_match = re.search(r"[Pp]illow\s*==\s*([\d.]+)", content)
            if pillow_match:
                pillow_version = pillow_match.group(1)
                # 简单的版本比较
                pillow_parts = pillow_version.split(".")
                min_parts = PILLOW_MIN_VERSION_PY312.split(".")

                # 如果 Pillow 版本小于 10.0.0
                if len(pillow_parts) >= 1:
                    try:
                        if int(pillow_parts[0]) < int(min_parts[0]):
                            warnings.append(
                                f"检测到 Pillow 版本 {pillow_version} 与 Python 3.12+ 不兼容\n"
                                f"  Pillow {PILLOW_MIN_VERSION_PY312}+ 才支持 Python 3.12+\n"
                                f"  建议使用系统 Pillow: sudo pacman -S python-pillow"
                            )
                    except ValueError:
                        pass
        except Exception:
            pass

    return warnings


def get_requirements_info(install_path: Path) -> dict:
    """获取 requirements 文件信息

    Args:
        install_path: OlivOS 安装路径

    Returns:
        包含文件路径、名称、Python版本信息的字典
    """
    requirements_file = get_requirements_file(install_path)

    return {
        "path": requirements_file,
        "name": requirements_file.name,
        "exists": requirements_file.exists(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "system": platform.system(),
        "warnings": check_requirements_compatibility(requirements_file),
    }
