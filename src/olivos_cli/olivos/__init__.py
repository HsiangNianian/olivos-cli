# -*- coding: utf-8 -*-
"""
OlivOS 配置交互模块
"""

import json
from pathlib import Path
from typing import Any, Optional

from ..core.config import expand_path
from ..core.exceptions import OlivOSConfigError
from ..core.logger import get_logger
from ..models import Account

logger = get_logger()


class OlivOSConfigManager:
    """OlivOS 配置管理器"""

    def __init__(self, root_path: Path):
        self.root_path = expand_path(str(root_path))
        self.conf_path = self.root_path / "conf"
        self.basic_file = self.conf_path / "basic.json"
        self.config_file = self.conf_path / "config.json"
        self.account_file = self.conf_path / "account.json"

    def ensure_dirs(self) -> None:
        """确保配置目录存在"""
        self.conf_path.mkdir(parents=True, exist_ok=True)

    def read_basic_config(self) -> dict:
        """读取 basic.json"""
        if not self.basic_file.exists():
            return {}
        try:
            with open(self.basic_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise OlivOSConfigError(f"读取 basic.json 失败: {e}") from e

    def write_basic_config(self, data: dict) -> None:
        """写入 basic.json"""
        self.ensure_dirs()
        try:
            with open(self.basic_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise OlivOSConfigError(f"写入 basic.json 失败: {e}") from e

    def read_config(self) -> dict:
        """读取 config.json"""
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise OlivOSConfigError(f"读取 config.json 失败: {e}") from e

    def write_config(self, data: dict) -> None:
        """写入 config.json"""
        self.ensure_dirs()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise OlivOSConfigError(f"写入 config.json 失败: {e}") from e

    def read_accounts(self) -> list[Account]:
        """读取账号列表"""
        if not self.account_file.exists():
            return []

        try:
            with open(self.account_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            accounts = []
            for acc_data in data.get("account", []):
                accounts.append(Account(
                    id=acc_data.get("id", ""),
                    password=acc_data.get("password", ""),
                    sdk_type=acc_data.get("sdk_type", ""),
                    platform_type=acc_data.get("platform_type", ""),
                    model_type=acc_data.get("model_type", "default"),
                    extends=acc_data.get("extends", {}),
                    debug=acc_data.get("debug", False),
                    server=acc_data.get("server", {}),
                ))
            return accounts
        except Exception as e:
            raise OlivOSConfigError(f"读取账号配置失败: {e}") from e

    def write_accounts(self, accounts: list[Account]) -> None:
        """写入账号列表"""
        self.ensure_dirs()

        try:
            data = {
                "account": [acc.to_dict() for acc in accounts]
            }
            with open(self.account_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise OlivOSConfigError(f"写入账号配置失败: {e}") from e

    def add_account(self, account: Account) -> None:
        """添加账号"""
        accounts = self.read_accounts()

        # 检查是否已存在（同一适配器下：platform + sdk + model 相同）
        for existing in accounts:
            if (str(existing.id) == str(account.id) and
                existing.platform_type == account.platform_type and
                existing.sdk_type == account.sdk_type and
                existing.model_type == account.model_type):
                raise OlivOSConfigError(
                    f"账号已存在: {account.id} (适配器: {account.platform_type}/{account.sdk_type}/{account.model_type})"
                )

        accounts.append(account)
        self.write_accounts(accounts)
        logger.success(f"账号已添加: {account.id}")

    def remove_account(self, account_id: int | str, sdk_type: Optional[str] = None) -> bool:
        """删除账号"""
        accounts = self.read_accounts()

        original_count = len(accounts)
        accounts = [
            acc for acc in accounts
            if not (str(acc.id) == str(account_id) and (sdk_type is None or acc.sdk_type == sdk_type))
        ]

        if len(accounts) < original_count:
            self.write_accounts(accounts)
            logger.success(f"账号已删除: {account_id}")
            return True

        return False

    def update_account(self, account_id: int | str, **kwargs) -> bool:
        """更新账号配置"""
        accounts = self.read_accounts()

        for acc in accounts:
            if str(acc.id) == str(account_id):
                for key, value in kwargs.items():
                    if hasattr(acc, key):
                        setattr(acc, key, value)
                self.write_accounts(accounts)
                logger.success(f"账号已更新: {account_id}")
                return True

        return False

    def get_account(self, account_id: int | str) -> Optional[Account]:
        """获取指定账号"""
        accounts = self.read_accounts()

        for acc in accounts:
            if str(acc.id) == str(account_id):
                return acc

        return None

    def list_accounts(self) -> list[Account]:
        """列出所有账号"""
        return self.read_accounts()

    def list_accounts_by_adapter(self, adapter_type: str) -> list[Account]:
        """按适配器类型列出账号"""
        from ..core.const import SUPPORTED_ADAPTERS

        if adapter_type not in SUPPORTED_ADAPTERS:
            return []

        sdk_type = SUPPORTED_ADAPTERS[adapter_type]["sdk_type"]
        accounts = self.read_accounts()
        return [acc for acc in accounts if acc.sdk_type == sdk_type]

    def count_accounts_by_adapter(self, adapter_type: str) -> int:
        """按适配器类型统计账号数量"""
        return len(self.list_accounts_by_adapter(adapter_type))

    def remove_accounts_by_adapter(self, adapter_type: str) -> int:
        """删除指定适配器类型的所有账号，返回删除数量"""
        from ..core.const import SUPPORTED_ADAPTERS

        if adapter_type not in SUPPORTED_ADAPTERS:
            return 0

        sdk_type = SUPPORTED_ADAPTERS[adapter_type]["sdk_type"]
        accounts = self.read_accounts()

        original_count = len(accounts)
        accounts = [acc for acc in accounts if acc.sdk_type != sdk_type]

        removed_count = original_count - len(accounts)
        if removed_count > 0:
            self.write_accounts(accounts)

        return removed_count

    def validate_account(self, account: Account) -> list[str]:
        """验证账号配置"""
        errors = []

        if not account.id:
            errors.append("账号 ID 不能为空")

        if not account.sdk_type:
            errors.append("sdk_type 不能为空")

        if not account.platform_type:
            errors.append("platform_type 不能为空")

        if account.server:
            if account.server.port and not (1 <= account.server.port <= 65535):
                errors.append(f"无效的端口号: {account.server.port}")

        return errors


from .account_api import OlivOSAccountAPI, get_account_api

__all__ = [
    "OlivOSConfigManager",
    "OlivOSAccountAPI",
    "get_account_api",
]
