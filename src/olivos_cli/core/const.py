"""
常量定义模块
"""

import os
import sys
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    _app_data = os.getenv("LOCALAPPDATA")
    if not _app_data:
        _app_data = Path.home() / "AppData" / "Local"
    else:
        _app_data = Path(_app_data)
    
    _base_dir = _app_data / "olivos-cli"
    
    CONFIG_DIR = _base_dir / "config"
    DATA_DIR = _base_dir / "data"
    CACHE_DIR = _base_dir / "cache"
    LOG_DIR = _base_dir / "log"
    
    # Windows 下 systemd 用户目录无意义，设为用户主目录
    SYSTEMD_USER_DIR = Path.home()
else:
    CONFIG_DIR = Path.home() / ".config" / "olivos-cli"
    DATA_DIR = Path.home() / ".local" / "share" / "olivos-cli"
    CACHE_DIR = Path.home() / ".cache" / "olivos-cli"
    LOG_DIR = Path.home() / ".local" / "state" / "olivos-cli"
    SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"

CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_SERVICE_NAME = "olivos-cli"
DEFAULT_BRANCH = "main"
DEFAULT_MIRROR_URL = "https://ghproxy.hydroroll.team"
DEFAULT_REPO_URL = "https://github.com/OlivOS-Team/OlivOS"

SUPPORTED_ADAPTERS = {
    "onebot": {
        "sdk_type": "onebot",
        "platform_type": "qq",
        "name": "OneBot V11",
        "description": "标准 OneBot V11 协议适配器",
    },
    "onebot12": {
        "sdk_type": "onebotV12",
        "platform_type": "qq",
        "name": "OneBot V12",
        "description": "标准 OneBot V12 协议适配器",
    },
    "telegram": {
        "sdk_type": "telegram_poll",
        "platform_type": "telegram",
        "name": "Telegram",
        "description": "Telegram Bot 适配器",
    },
    "discord": {
        "sdk_type": "discord",
        "platform_type": "discord",
        "name": "Discord",
        "description": "Discord Bot 适配器",
    },
    "qqguild": {
        "sdk_type": "qqGuild",
        "platform_type": "qqGuild",
        "name": "QQ 频道",
        "description": "QQ 频道适配器",
    },
    "qqguildv2": {
        "sdk_type": "qqGuildv2",
        "platform_type": "qqGuild",
        "name": "QQ 频道 V2",
        "description": "QQ 频道 V2 适配器",
    },
    "dingtalk": {
        "sdk_type": "dingtalk",
        "platform_type": "dingtalk",
        "name": "钉钉",
        "description": "钉钉机器人适配器",
    },
    "kaiheila": {
        "sdk_type": "kaiheila",
        "platform_type": "kaiheila",
        "name": "开黑啦",
        "description": "开黑啦适配器",
    },
    "dodo": {
        "sdk_type": "dodo",
        "platform_type": "dodo",
        "name": "DoDo",
        "description": "DoDo 适配器",
    },
    "fanbook": {
        "sdk_type": "fanbook",
        "platform_type": "fanbook",
        "name": "Fanbook",
        "description": "Fanbook 适配器",
    },
    "mhyvila": {
        "sdk_type": "mhyVila",
        "platform_type": "mhyVila",
        "name": "米游社大别野",
        "description": "米游社大别野适配器",
    },
    "bililive": {
        "sdk_type": "biliLive",
        "platform_type": "biliLive",
        "name": "哔哩哔哩直播",
        "description": "哔哩哔哩直播适配器",
    },
    "xiaoheihe": {
        "sdk_type": "xiaoheihe",
        "platform_type": "xiaoheihe",
        "name": "小黑盒",
        "description": "小黑盒适配器",
    },
    "virtual": {
        "sdk_type": "virtualTerminal",
        "platform_type": "virtual",
        "name": "虚拟终端",
        "description": "虚拟终端适配器（用于测试）",
    },
}

ADAPTER_TYPE_CHOICES = list(SUPPORTED_ADAPTERS.keys())
PACKAGE_MANAGERS = ["uv", "pip", "poetry", "rye", "pdm"]
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
