# -*- coding: utf-8 -*-
"""
账号配置校验模块

根据 OlivOS 官方文档定义的规则校验账号配置
https://doc.olivos.wiki/User/Account/
"""

from dataclasses import dataclass, field
from typing import Any

from .adapters import ALL_ADAPTERS, get_adapter_config
from .logger import get_logger

logger = get_logger()


@dataclass
class ValidationResult:
    """校验结果"""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str):
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        self.warnings.append(message)


def validate_account_config(account_data: dict, adapter_key: str | None = None) -> ValidationResult:
    """校验账号配置

    Args:
        account_data: 账号配置字典
        adapter_key: 适配器键值（如果已知）

    Returns:
        ValidationResult 校验结果
    """
    result = ValidationResult(valid=True)

    # 基础字段校验
    if "id" not in account_data or not account_data["id"]:
        result.add_error("缺少必填字段: id")
    if "platform_type" not in account_data or not account_data["platform_type"]:
        result.add_error("缺少必填字段: platform_type")
    if "sdk_type" not in account_data or not account_data["sdk_type"]:
        result.add_error("缺少必填字段: sdk_type")
    if "model_type" not in account_data:
        account_data["model_type"] = "default"

    # 如果指定了适配器，使用适配器规则校验
    if adapter_key:
        adapter = get_adapter_config(adapter_key)
        if adapter:
            return _validate_with_adapter(account_data, adapter)

    # 尝试根据 platform_type + sdk_type + model_type 查找适配器
    platform = account_data.get("platform_type", "")
    sdk = account_data.get("sdk_type", "")
    model = account_data.get("model_type", "default")

    for adapter in ALL_ADAPTERS.values():
        if (adapter.platform_type == platform and
            adapter.sdk_type == sdk and
            adapter.model_type == model):
            return _validate_with_adapter(account_data, adapter)

    # 未找到匹配的适配器配置，进行基础校验
    return _validate_basic(account_data, result)


def _validate_with_adapter(account_data: dict, adapter) -> ValidationResult:
    """使用适配器配置校验"""
    result = ValidationResult(valid=True)

    # 检查所需字段
    for field in adapter.required_fields:
        if "." in field:
            # 嵌套字段，如 server.host
            parts = field.split(".")
            obj = account_data
            for i, part in enumerate(parts):
                if part not in obj:
                    if i == len(parts) - 1:
                        result.add_error(f"缺少必填字段: {field}")
                    break
                obj = obj[part]
            else:
                # 检查是否为空
                if obj[parts[-1]] == "" and field not in adapter.optional_fields:
                    result.add_warning(f"字段 {field} 建议填写")
        else:
            if field not in account_data:
                result.add_error(f"缺少必填字段: {field}")
            elif account_data[field] == "" and field not in adapter.optional_fields:
                result.add_warning(f"字段 {field} 建议填写")

    # 检查 server 配置
    if "server" in account_data and account_data["server"]:
        server = account_data["server"]
        # server 可能是 dict 或 AccountServer 对象
        if hasattr(server, 'to_dict'):
            server = server.to_dict()
        server_type = server.get("type", adapter.server_type.value)

        # WebSocket 类型需要 host 和 port
        if server_type == "websocket":
            if not server.get("host") and not server.get("url"):
                if adapter.server_auto:
                    # 自动模式下可以不填
                    pass
                else:
                    result.add_error("WebSocket 类型需要 server.host 或 server.url")

        # POST 类型通常需要 host 和 port
        if server_type == "post":
            if not adapter.server_auto:
                if not server.get("host"):
                    result.add_error("POST 类型需要 server.host")
                if not server.get("port"):
                    result.add_error("POST 类型需要 server.port")

    # 特殊校验规则
    _validate_special_rules(account_data, adapter, result)

    return result


def _validate_special_rules(account_data: dict, adapter, result: ValidationResult):
    """特殊适配器的校验规则"""

    # Telegram 特殊规则：id 和 access_token 格式
    if adapter.key == "telegram":
        id_val = str(account_data.get("id", ""))
        if not ":" in id_val:
            result.add_warning("Telegram token 格式通常为 id:token")

    # QQ 官方频道 V2 intents 检查
    if adapter.key == "qqguild_v2":
        model = account_data.get("model_type", "")
        if "intents" in model:
            if "extends" not in account_data or "intents" not in account_data.get("extends", {}):
                result.add_warning("指定 intents 模式需要在 extends 中配置 intents 字段")

    # 米游社大别野沙盒模式检查
    if adapter.key == "mhyvila":
        model = account_data.get("model_type", "")
        if model == "sandbox":
            if "server" not in account_data or not account_data["server"].get("port"):
                result.add_error("沙盒模式需要填写 server.port (别野号)")

    # B站直播间游客模式提示
    if adapter.key == "bililive":
        model = account_data.get("model_type", "")
        if model == "default":
            result.add_warning("游客模式只能浏览弹幕，不能发送消息")


def _validate_basic(account_data: dict, result: ValidationResult) -> ValidationResult:
    """基础校验（无适配器配置）"""
    # 检查 server 配置
    if "server" in account_data and account_data["server"]:
        server = account_data["server"]
        # server 可能是 dict 或 AccountServer 对象
        if hasattr(server, 'to_dict'):
            server = server.to_dict()

        # 检查 server.type
        if "type" not in server:
            result.add_error("server 缺少 type 字段")

        # 检查必要的服务器配置
        if server.get("auto") is False:
            if not server.get("host") and not server.get("url"):
                result.add_warning("非自动模式建议配置 server.host 或 server.url")
            if server.get("type") == "post" and not server.get("port"):
                result.add_warning("POST 类型建议配置 server.port")

    return result


def validate_extends(adapter_key: str, extends: dict) -> ValidationResult:
    """校验扩展字段

    Args:
        adapter_key: 适配器键值
        extends: 扩展字段字典

    Returns:
        ValidationResult 校验结果
    """
    result = ValidationResult(valid=True)

    adapter = get_adapter_config(adapter_key)
    if not adapter or not adapter.extends_options:
        return result

    for key, value in extends.items():
        if key not in adapter.extends_options:
            result.add_warning(f"未知的扩展字段: {key}")
        else:
            # 检查类型
            expected_type = adapter.extends_options[key].get("type")
            if expected_type == "string":
                if not isinstance(value, str):
                    result.add_error(f"扩展字段 {key} 应为字符串类型")

    return result


def get_adapter_required_fields(adapter_key: str) -> list[str]:
    """获取适配器的必填字段列表"""
    adapter = get_adapter_config(adapter_key)
    if adapter:
        return adapter.required_fields.copy()
    return []


def get_adapter_optional_fields(adapter_key: str) -> list[str]:
    """获取适配器的可选字段列表"""
    adapter = get_adapter_config(adapter_key)
    if adapter:
        return adapter.optional_fields.copy()
    return []


def get_adapter_model_type_options(adapter_key: str) -> dict[str, str]:
    """获取适配器的 model_type 选项"""
    adapter = get_adapter_config(adapter_key)
    if adapter:
        return adapter.model_type_options.copy()
    return {}


def get_adapter_extends_options(adapter_key: str) -> dict[str, dict]:
    """获取适配器的扩展字段选项"""
    adapter = get_adapter_config(adapter_key)
    if adapter:
        return adapter.extends_options.copy()
    return {}
