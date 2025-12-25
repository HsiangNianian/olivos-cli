# -*- coding: utf-8 -*-
"""
OlivOS 账号类型配置读取模块

从 OlivOS 的 accountMetadataAPI.py 读取预配置的账号类型模板
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.logger import get_logger

logger = get_logger()


@dataclass
class AccountTypeConfig:
    """账号类型配置"""

    name: str  # 显示名称
    platform: str  # 平台类型
    sdk: str  # SDK 类型
    model: str  # 模型类型
    server_auto: bool  # 服务器自动模式
    server_type: str  # 服务器类型 (post/websocket)


@dataclass
class AdapterTypeInfo:
    """适配器类型信息"""

    name: str  # 显示名称
    platform: str  # 平台类型
    sdk: str  # SDK 类型
    available_models: list[str]  # 可用的 model 类型


class OlivOSAccountAPI:
    """OlivOS 账号 API 读取器"""

    def __init__(self, olivos_path: Path):
        self.olivos_path = olivos_path
        # 尝试多个可能的路径
        possible_paths = [
            olivos_path / "OlivOS" / "core" / "core" / "accountMetadataAPI.py",
            olivos_path / "OlivOS" / "OlivOS" / "core" / "core" / "accountMetadataAPI.py",
            olivos_path / "core" / "core" / "accountMetadataAPI.py",
        ]
        for path in possible_paths:
            if path.exists():
                self.account_api_file = path
                break
        else:
            self.account_api_file = olivos_path / "OlivOS" / "core" / "core" / "accountMetadataAPI.py"
        self._account_type_mapping: dict[str, AccountTypeConfig] | None = None
        self._adapter_types: dict[str, dict[str, list[str]]] | None = None

    def _read_file(self) -> str:
        """读取 accountMetadataAPI.py 文件"""
        if not self.account_api_file.exists():
            raise FileNotFoundError(f"OlivOS accountMetadataAPI.py 不存在: {self.account_api_file}")

        with open(self.account_api_file, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_account_type_mapping(self, content: str) -> dict[str, AccountTypeConfig]:
        """解析 accountTypeMappingList"""
        if self._account_type_mapping is not None:
            return self._account_type_mapping

        # 找到 accountTypeMappingList = { 的位置
        start_marker = "accountTypeMappingList = {"
        start_idx = content.find(start_marker)
        if start_idx == -1:
            logger.warning_print("未找到 accountTypeMappingList")
            return {}

        # 从起始位置开始，手动匹配花括号
        brace_count = 0
        in_dict = False
        end_idx = start_idx + len(start_marker) - 1  # 包含起始的 {

        for i in range(start_idx + len(start_marker) - 1, len(content)):
            if content[i] == '{':
                brace_count += 1
                in_dict = True
            elif content[i] == '}':
                brace_count -= 1
                if in_dict and brace_count == 0:
                    end_idx = i + 1
                    break

        dict_content = content[start_idx + len("accountTypeMappingList"):end_idx].strip()
        if not dict_content.startswith('='):
            logger.warning_print("accountTypeMappingList 格式错误")
            return {}
        dict_content = dict_content[1:].strip()  # 移除 '='

        # 使用 ast 安全解析
        try:
            tree = ast.parse(dict_content, mode="eval")
            mapping_dict = ast.literal_eval(tree)

            result = {}
            for name, config in mapping_dict.items():
                result[name] = AccountTypeConfig(
                    name=name,
                    platform=config[0],
                    sdk=config[1],
                    model=config[2],
                    server_auto=str(config[3]).lower() == "true",
                    server_type=config[4],
                )

            self._account_type_mapping = result
            return result

        except Exception as e:
            logger.warning_print(f"解析 accountTypeMappingList 失败: {e}")
            return {}

    def _parse_adapter_types(self, content: str) -> dict[str, dict[str, list[str]]]:
        """解析适配器类型信息（返回 platform: {sdk: [models]}）"""
        if self._adapter_types is not None:
            return self._adapter_types

        # 提取 accountTypeDataList_platform_sdk_model
        start_marker = "accountTypeDataList_platform_sdk_model = {"
        start_idx = content.find(start_marker)
        if start_idx == -1:
            logger.warning_print("未找到 accountTypeDataList_platform_sdk_model")
            return {}

        brace_count = 0
        in_dict = False
        end_idx = start_idx + len(start_marker) - 1

        for i in range(start_idx + len(start_marker) - 1, len(content)):
            if content[i] == '{':
                brace_count += 1
                in_dict = True
            elif content[i] == '}':
                brace_count -= 1
                if in_dict and brace_count == 0:
                    end_idx = i + 1
                    break

        dict_content = content[start_idx + len("accountTypeDataList_platform_sdk_model"):end_idx].strip()
        if not dict_content.startswith('='):
            logger.warning_print("accountTypeDataList_platform_sdk_model 格式错误")
            return {}
        dict_content = dict_content[1:].strip()  # 移除 '='

        try:
            tree = ast.parse(dict_content, mode="eval")
            platform_sdk_model = ast.literal_eval(tree)

            self._adapter_types = platform_sdk_model
            return platform_sdk_model

        except Exception as e:
            logger.warning_print(f"解析 accountTypeDataList_platform_sdk_model 失败: {e}")
            return {}

    def _get_adapter_name(self, platform: str, sdk: str, model: str) -> str:
        """获取适配器显示名称"""
        # 映射表
        platform_names = {
            "qq": "QQ",
            "wechat": "微信",
            "qqGuild": "QQ频道",
            "kaiheila": "KOOK",
            "xiaoheihe": "小黑盒",
            "mhyVila": "米游社大别野",
            "telegram": "Telegram",
            "dodo": "Dodo",
            "fanbook": "Fanbook",
            "discord": "Discord",
            "terminal": "虚拟终端",
            "hackChat": "Hack.Chat",
            "biliLive": "B站直播间",
            "dingtalk": "钉钉",
        }

        model_names = {
            "default": "默认",
            "public": "公域",
            "private": "私域",
            "sandbox": "沙盒",
            "login": "登录",
            "postapi": "接口终端",
            "ff14": "FF14终端",
        }

        platform_name = platform_names.get(platform, platform)
        model_name = model_names.get(model, model)

        if model == "default":
            return platform_name
        return f"{platform_name} ({model_name})"

    def get_account_types(self) -> dict[str, AccountTypeConfig]:
        """获取所有账号类型配置"""
        content = self._read_file()
        return self._parse_account_type_mapping(content)

    def get_adapter_types(self) -> dict[str, list[AdapterTypeInfo]]:
        """获取适配器类型（按平台分组）"""
        content = self._read_file()
        return self._parse_adapter_types(content)

    def get_predefined_templates(self, platform: str | None = None) -> list[AccountTypeConfig]:
        """获取预定义的账号类型模板

        Args:
            platform: 可选，过滤指定平台的模板
        """
        mapping = self.get_account_types()
        if platform:
            return [cfg for cfg in mapping.values() if cfg.platform == platform]
        return list(mapping.values())

    def get_platform_list(self) -> list[str]:
        """获取平台列表"""
        content = self._read_file()

        # 提取 accountTypeDataList_platform
        start_marker = "accountTypeDataList_platform = ["
        start_idx = content.find(start_marker)
        if start_idx == -1:
            logger.warning_print("未找到 accountTypeDataList_platform")
            return []

        # 找到列表结束位置（使用方括号匹配）
        bracket_count = 0
        in_list = False
        end_idx = start_idx + len(start_marker) - 1  # 包含起始的 [

        for i in range(start_idx + len(start_marker) - 1, len(content)):
            if content[i] == '[':
                bracket_count += 1
                in_list = True
            elif content[i] == ']':
                bracket_count -= 1
                if in_list and bracket_count == 0:
                    end_idx = i + 1
                    break

        # 提取列表内容
        list_content = content[start_idx + len("accountTypeDataList_platform"):end_idx].strip()
        if not list_content.startswith('='):
            logger.warning_print("accountTypeDataList_platform 格式错误")
            return []
        list_content = list_content[1:].strip()  # 移除 '='

        try:
            tree = ast.parse(list_content, mode="eval")
            platform_list = ast.literal_eval(tree)
            return platform_list
        except Exception as e:
            logger.warning_print(f"解析 accountTypeDataList_platform 失败: {e}")
            return []

    def get_platform_sdk_model(self) -> dict:
        """获取平台-SDK-模型的映射关系"""
        content = self._read_file()
        return self._parse_adapter_types(content)


def get_account_api(olivos_path: Path) -> OlivOSAccountAPI:
    """获取 OlivOS 账号 API 读取器"""
    return OlivOSAccountAPI(olivos_path)
