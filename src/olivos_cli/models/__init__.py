# -*- coding: utf-8 -*-
"""
数据模型模块
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Account:
    """OlivOS 账号模型"""

    id: int | str
    password: str
    sdk_type: str
    platform_type: str
    model_type: str = "default"
    extends: dict[str, Any] = field(default_factory=dict)
    debug: bool = False
    server: "AccountServer" = None

    def __post_init__(self):
        if self.server is None:
            self.server = AccountServer()
        elif isinstance(self.server, dict):
            self.server = AccountServer(**self.server)

    def to_dict(self) -> dict:
        """转换为字典"""
        from dataclasses import asdict

        return asdict(self)


@dataclass
class AccountServer:
    """账号服务器配置"""

    auto: bool = True
    type: str = "post"
    host: str = "127.0.0.1"
    port: int = 57000
    access_token: str = ""
    url: str = ""

    def to_dict(self) -> dict:
        """转换���字典"""
        from dataclasses import asdict

        return asdict(self)


@dataclass
class AdapterConfig:
    """适配器配置模型"""

    name: str
    sdk_type: str
    platform_type: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceStatus:
    """服务状态模型"""

    name: str
    loaded: bool = False
    active: bool = False
    running: bool = False
    enabled: bool = False
    pid: Optional[int] = None
    memory: Optional[str] = None
    uptime: Optional[str] = None


@dataclass
class InstanceInfo:
    """实例信息模型"""

    name: str
    path: str
    branch: str
    service_name: str
    enabled: bool
    running: bool
    version: Optional[str] = None
