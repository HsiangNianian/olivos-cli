# -*- coding: utf-8 -*-
"""
自定义异常模块
"""


class OlivOSCLIError(Exception):
    """OlivOS-CLI 基础异常"""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)


class ConfigError(OlivOSCLIError):
    """配置相关异常"""


class GitError(OlivOSCLIError):
    """Git 操作相关异常"""


class PackageError(OlivOSCLIError):
    """包管理相关异常"""


class SystemdError(OlivOSCLIError):
    """systemd 相关异常"""


class OlivOSConfigError(OlivOSCLIError):
    """OlivOS 配置相关异常"""


class AccountError(OlivOSCLIError):
    """账号相关异常"""


class AdapterError(OlivOSCLIError):
    """适配器相关异常"""


class ValidationError(OlivOSCLIError):
    """验证相关异常"""


class FileNotFoundError(OlivOSCLIError):
    """文件未找到异常"""


class ProcessError(OlivOSCLIError):
    """进程执行相关异常"""
