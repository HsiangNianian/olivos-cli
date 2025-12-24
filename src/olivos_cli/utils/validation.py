# -*- coding: utf-8 -*-
"""
验证工具
"""

import re
from typing import Any, Optional


def validate_port(port: Any) -> bool:
    """验证端口号"""
    try:
        p = int(port)
        return 1 <= p <= 65535
    except (ValueError, TypeError):
        return False


def validate_url(url: str) -> bool:
    """验证 URL 格式"""
    if not url:
        return False
    try:
        from urllib.parse import urlparse

        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_account_id(account_id: Any) -> bool:
    """验证账号 ID 格式"""
    if isinstance(account_id, int):
        return account_id > 0
    if isinstance(account_id, str):
        try:
            return int(account_id) > 0
        except ValueError:
            return False
    return False


def validate_git_branch(branch: str) -> bool:
    """验证 Git 分支名"""
    if not branch:
        return False
    # Git 分支名规则
    pattern = r"^[a-zA-Z0-9_\-./]+$"
    return bool(re.match(pattern, branch))


def validate_commit_hash(hash_str: str) -> bool:
    """验证 Git commit hash"""
    if not hash_str:
        return False
    # 7-40 位的十六进制
    pattern = r"^[0-9a-fA-F]{7,40}$"
    return bool(re.match(pattern, hash_str))


__all__ = [
    "validate_port",
    "validate_url",
    "validate_email",
    "validate_account_id",
    "validate_git_branch",
    "validate_commit_hash",
]
