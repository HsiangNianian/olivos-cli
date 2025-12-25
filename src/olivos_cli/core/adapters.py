# -*- coding: utf-8 -*-
"""
适配器配置定义模块

根据 OlivOS 实际代码定义的 16 个适配器模块
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .logger import get_logger

logger = get_logger()


class ServerType(str, Enum):
    """服务器对接类型"""
    POST = "post"
    WEBSOCKET = "websocket"


@dataclass
class AdapterConfig:
    """适配器配置定义"""

    # 适配器标识
    name: str  # 显示名称
    key: str  # 唯一标识符

    # 固定配置
    platform_type: str
    sdk_type: str
    model_type: str = "default"
    server_auto: bool = True
    server_type: ServerType = ServerType.POST

    # 所需配置字段
    required_fields: list[str] = field(default_factory=list)

    # 可选配置字段
    optional_fields: list[str] = field(default_factory=list)

    # model_type 选项（如果有多个）
    model_type_options: dict[str, str] = field(default_factory=dict)

    # 扩展字段选项
    extends_options: dict[str, dict] = field(default_factory=dict)

    # 描述
    description: str = ""

    # 帮助信息
    help_text: str = ""

# 1. onebotV11 - QQ 平台
ONEBOTV11_MODEL_TYPES = {
    "default": "默认模式",
    "napcat": "NapCat",
    "napcat_hide": "NapCat (隐藏)",
    "napcat_show": "NapCat (显示)",
    "napcat_show_new": "NapCat (新版)",
    "napcat_show_old": "NapCat (旧版)",
    "napcat_default": "NapCat (默认)",
    "shamrock_default": "Shamrock (默认)",
    "para_default": "Para 消息模式",
    "gocqhttp_show": "GoCqHttp",
    "gocqhttp_show_Android_Phone": "GoCqHttp (安卓手机)",
    "gocqhttp_show_Android_Pad": "GoCqHttp (安卓平板)",
    "gocqhttp_show_Android_Watch": "GoCqHttp (安卓手表)",
    "gocqhttp_show_iPad": "GoCqHttp (iPad)",
    "gocqhttp_show_iMac": "GoCqHttp (iMac)",
    "gocqhttp_show_old": "GoCqHttp (旧版)",
    "walleq_show": "WalleQ",
    "walleq_show_Android_Phone": "WalleQ (安卓手机)",
    "walleq_show_Android_Pad": "WalleQ (安卓平板)",
    "walleq_show_Android_Watch": "WalleQ (安卓手表)",
    "walleq_show_iPad": "WalleQ (iPad)",
    "walleq_show_iMac": "WalleQ (iMac)",
    "walleq_show_old": "WalleQ (旧版)",
    "llonebot_default": "LLOneBot",
    "lagrange_default": "Lagrange",
}

# 2. onebotV12 - QQ 平台
ONEBOTV12_MODEL_TYPES = {
    "onebotV12": "OneBot 12",
}

# 3. qqGuild - QQ 频道
QQGUILD_MODEL_TYPES = {
    "default": "QQ 频道 V1",
    "public": "QQ 频道 V1 (公域)",
    "private": "QQ 频道 V1 (私域)",
}

QQGUILV2_MODEL_TYPES = {
    "default": "QQ 频道 V2",
    "public": "QQ 频道 V2 (公域)",
    "public_guild_only": "QQ 频道 V2 (纯频道)",
    "public_intents": "QQ 频道 V2 (指定intents)",
    "private": "QQ 频道 V2 (私域)",
    "private_intents": "QQ 频道 V2 (私域+intents)",
}

# 4. OPQBot - QQ 平台
OPQBOT_MODEL_TYPES = {
    "opqbot_default": "OPQBot (默认)",
    "opqbot_port": "OPQBot (指定端口)",
    "opqbot_port_old": "OPQBot (指定端口/旧)",
}

# 5. red - QQ 平台 (Chronocat RED 协议)
RED_MODEL_TYPES = {
    "red": "RED 协议",
}

# 6. telegram
TELEGRAM_MODEL_TYPES = {
    "default": "Telegram Bot",
}

# 7. discord
DISCORD_MODEL_TYPES = {
    "default": "Discord Bot",
}

# 8. kaiheila (KOOK)
KAIHEILA_MODEL_TYPES = {
    "default": "KOOK",
    "text": "KOOK (消息兼容)",
}

# 9. dingtalk
DINGTALK_MODEL_TYPES = {
    "default": "钉钉开放平台",
}

# 10. biliLive
BILILIVE_MODEL_TYPES = {
    "default": "游客模式",
    "login": "登录模式",
}

# 11. mhyVila (米游社大别野)
MHYVILA_MODEL_TYPES = {
    "default": "米游社大别野",
    "public": "公域",
    "private": "私域",
}

# 12. dodo
DODO_MODEL_TYPES = {
    "default": "Dodo V2",
    "v1": "Dodo V1",
}

# 13. fanbook
FANBOOK_MODEL_TYPES = {
    "default": "Fanbook 开放平台",
}

# 14. hackChat
HACKCHAT_MODEL_TYPES = {
    "default": "Hack.Chat",
    "private": "Hack.Chat (私有)",
}

# 15. xiaoheihe (小黑盒)
XIAOHEIHE_MODEL_TYPES = {
    "default": "小黑盒开放平台",
}

# 16. virtualTerminal
VIRTUAL_TERMINAL_MODEL_TYPES = {
    "default": "虚拟终端",
    "postapi": "HTTP 接口终端",
    "ff14": "FF14 终端",
}

ALL_ADAPTERS: dict[str, AdapterConfig] = {
    # 1. onebotV11 - QQ 平台
    "onebotV11": AdapterConfig(
        name="OneBot V11 (QQ)",
        key="onebotV11",
        platform_type="qq",
        sdk_type="onebot",
        model_type="default",
        server_auto=True,
        server_type=ServerType.POST,
        required_fields=["id"],
        optional_fields=["password", "server.access_token"],
        model_type_options=ONEBOTV11_MODEL_TYPES,
        description="OneBot 11 协议适配器",
        help_text="支持 NapCat、GoCqHttp、WalleQ、Shamrock、LLOneBot、Lagrange 等实现",
    ),

    # 2. onebotV12 - QQ 平台
    "onebotV12": AdapterConfig(
        name="OneBot V12 (QQ)",
        key="onebotV12",
        platform_type="qq",
        sdk_type="onebot",
        model_type="onebotV12",
        server_auto=False,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "server.host", "server.port"],
        optional_fields=["server.access_token"],
        model_type_options=ONEBOTV12_MODEL_TYPES,
        description="OneBot 12 协议适配器",
        help_text="适用于 Walle-Q、ComWeChatBot 等",
    ),

    # 3. qqGuild - QQ 频道 V1
    "qqGuild": AdapterConfig(
        name="QQ 频道",
        key="qqGuild",
        platform_type="qqGuild",
        sdk_type="qqGuild_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "server.access_token"],
        optional_fields=["password"],
        model_type_options=QQGUILD_MODEL_TYPES,
        description="QQ 频道开放平台",
        help_text="V1 版本接口",
    ),

    # 3b. qqGuildV2 - QQ 频道 V2
    "qqGuildV2": AdapterConfig(
        name="QQ 频道 V2",
        key="qqGuildV2",
        platform_type="qqGuild",
        sdk_type="qqGuildv2_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "server.access_token"],
        optional_fields=["password"],
        model_type_options=QQGUILV2_MODEL_TYPES,
        description="QQ 频道开放平台 V2",
        help_text="V2 版本接口，支持 QQ 群官方机器人",
    ),

    # 4. OPQBot - QQ 平台
    "OPQBot": AdapterConfig(
        name="OPQBot (QQ)",
        key="OPQBot",
        platform_type="qq",
        sdk_type="onebot",
        model_type="opqbot_default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "password"],
        model_type_options=OPQBOT_MODEL_TYPES,
        description="OPQBot 远程协议端",
        help_text="注意：需要向 OPQ 官方申请 Token，账号存在安全风险",
    ),

    # 5. red - QQ 平台 (Chronocat)
    "red": AdapterConfig(
        name="RED 协议 (QQ)",
        key="red",
        platform_type="qq",
        sdk_type="onebot",
        model_type="red",
        server_auto=False,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "server.host", "server.port", "server.access_token"],
        optional_fields=["extends.http-path"],
        model_type_options=RED_MODEL_TYPES,
        extends_options={
            "http-path": {"type": "string", "description": "HTTP 地址"}
        },
        description="Chronocat RED 协议",
        help_text="注意：Chronocat 已停止维护",
    ),

    # 6. telegram
    "telegram": AdapterConfig(
        name="Telegram",
        key="telegram",
        platform_type="telegram",
        sdk_type="telegram_poll",
        model_type="default",
        server_auto=True,
        server_type=ServerType.POST,
        required_fields=["id", "server.access_token"],
        model_type_options=TELEGRAM_MODEL_TYPES,
        description="Telegram Bot",
        help_text="通过 @botfather 创建机器人，格式: id:token",
    ),

    # 7. discord
    "discord": AdapterConfig(
        name="Discord",
        key="discord",
        platform_type="discord",
        sdk_type="discord_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["server.access_token"],
        optional_fields=["id"],
        model_type_options=DISCORD_MODEL_TYPES,
        description="Discord Bot",
        help_text="从 Discord 开发者平台获取 Token",
    ),

    # 8. kaiheila (KOOK)
    "kaiheila": AdapterConfig(
        name="KOOK",
        key="kaiheila",
        platform_type="kaiheila",
        sdk_type="kaiheila_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["server.access_token"],
        model_type_options=KAIHEILA_MODEL_TYPES,
        description="KOOK 开放平台",
        help_text="消息兼容模式以纯文本发送，可解决权限问题",
    ),

    # 9. dingtalk
    "dingtalk": AdapterConfig(
        name="钉钉",
        key="dingtalk",
        platform_type="dingtalk",
        sdk_type="dingtalk_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id"],
        model_type_options=DINGTALK_MODEL_TYPES,
        description="钉钉开放平台",
        help_text="id 为机器人账号的 Robot Code",
    ),

    # 10. biliLive
    "biliLive": AdapterConfig(
        name="B站直播间",
        key="biliLive",
        platform_type="biliLive",
        sdk_type="biliLive_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["server.access_token"],
        model_type_options=BILILIVE_MODEL_TYPES,
        description="B站直播间弹幕系统",
        help_text="游客模式只能浏览，登录模式可发送消息",
    ),

    # 11. mhyVila (米游社大别野)
    "mhyVila": AdapterConfig(
        name="米游社大别野",
        key="mhyVila",
        platform_type="mhyVila",
        sdk_type="mhyVila_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "password", "server.access_token"],
        optional_fields=["server.port"],
        model_type_options=MHYVILA_MODEL_TYPES,
        description="米游社大别野开放平台",
        help_text="server.port 仅沙盒模式需要填写别野号",
    ),

    # 12. dodo
    "dodo": AdapterConfig(
        name="Dodo",
        key="dodo",
        platform_type="dodo",
        sdk_type="dodo_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "server.access_token"],
        model_type_options=DODO_MODEL_TYPES,
        description="Dodo 开放平台",
        help_text="提供 V1、V2 两个版本的接口",
    ),

    # 13. fanbook
    "fanbook": AdapterConfig(
        name="Fanbook",
        key="fanbook",
        platform_type="fanbook",
        sdk_type="fanbook_poll",
        model_type="default",
        server_auto=True,
        server_type=ServerType.POST,
        required_fields=["server.access_token"],
        model_type_options=FANBOOK_MODEL_TYPES,
        description="Fanbook 开放平台",
        help_text="从 Fanbook 获取 Token",
    ),

    # 14. hackChat
    "hackChat": AdapterConfig(
        name="Hack.Chat",
        key="hackChat",
        platform_type="hackChat",
        sdk_type="hackChat_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id", "server.access_token", "password"],
        optional_fields=["extends.ws_path"],
        model_type_options=HACKCHAT_MODEL_TYPES,
        extends_options={
            "ws_path": {"type": "string", "description": "私有 Websocket 服务器地址"}
        },
        description="Hack.Chat 聊天协议",
        help_text="id 为房间名称，server.access_token 为 Bot 名称",
    ),

    # 15. xiaoheihe (小黑盒)
    "xiaoheihe": AdapterConfig(
        name="小黑盒",
        key="xiaoheihe",
        platform_type="xiaoheihe",
        sdk_type="xiaoheihe_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["server.access_token"],
        model_type_options=XIAOHEIHE_MODEL_TYPES,
        description="小黑盒开放平台",
        help_text="从小黑盒获取 Token",
    ),

    # 16. virtualTerminal
    "virtualTerminal": AdapterConfig(
        name="虚拟终端",
        key="virtualTerminal",
        platform_type="terminal",
        sdk_type="terminal_link",
        model_type="default",
        server_auto=True,
        server_type=ServerType.WEBSOCKET,
        required_fields=["id"],
        model_type_options=VIRTUAL_TERMINAL_MODEL_TYPES,
        description="虚拟聊天终端",
        help_text="用于插件调试和测试",
    ),
}

ADAPTER_GROUPS: dict[str, list[str]] = {
    "QQ 平台": ["onebotV11", "onebotV12", "qqGuild", "qqGuildV2", "OPQBot", "red"],
    "通讯软件": ["telegram", "discord", "kaiheila", "dingtalk", "fanbook"],
    "直播/游戏": ["biliLive", "mhyVila", "dodo", "xiaoheihe"],
    "其他": ["hackChat", "virtualTerminal"],
}


def get_adapter_config(key: str) -> AdapterConfig | None:
    """获取适配器配置"""
    return ALL_ADAPTERS.get(key)


def get_adapter_by_platform_sdk(platform: str, sdk: str, model: str) -> AdapterConfig | None:
    """根据 platform_type、sdk_type、model_type 查找适配器"""
    for config in ALL_ADAPTERS.values():
        if (config.platform_type == platform and
            config.sdk_type == sdk and
            config.model_type == model):
            return config
    return None


def list_adapter_configs() -> list[AdapterConfig]:
    """列出所有适配器配置"""
    return list(ALL_ADAPTERS.values())


def get_adapter_choices() -> list[tuple[str, str]]:
    """获取适配器选择列表 [(key, name), ...]"""
    return [(key, config.name) for key, config in ALL_ADAPTERS.items()]
