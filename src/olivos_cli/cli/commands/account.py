# -*- coding: utf-8 -*-
"""
account 命令实现
"""

from ...core import (
    ADAPTER_GROUPS,
    get_adapter_by_platform_sdk,
    get_adapter_config,
    get_adapter_extends_options,
    get_adapter_model_type_options,
    get_logger,
)
from ...core.exceptions import OlivOSConfigError
from ...olivos import OlivOSConfigManager
from ...models import Account, AccountServer
from ...utils.prompt import ask, confirm, select, select_multiple

logger = get_logger()


def cmd_account(config_manager, args) -> int:
    """账号管理"""
    action = args.acc_action

    if not action:
        # 显示帮助信息
        logger.info_print("用法: olivos-cli account [ACTION] [OPTIONS]")
        logger.info_print("")
        logger.info_print("动作:")
        logger.info_print("  list (ls)     列出所有账号")
        logger.info_print("  add           添加账号")
        logger.info_print("  remove (rm)   删除账号")
        logger.info_print("  show          显示账号详情")
        logger.info_print("")
        logger.info_print("使用 'olivos-cli account [ACTION] --help' 查看具体动作的帮助")
        return 0

    config = config_manager.config
    install_path = config.git.expanded_install_path

    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        logger.info_print("请先运行: olivos-cli init")
        return 1

    olivos_config = OlivOSConfigManager(install_path)

    if action == "list":
        return _cmd_account_list(olivos_config)
    elif action == "add":
        return _cmd_account_add(olivos_config, args)
    elif action == "remove":
        return _cmd_account_remove(olivos_config, args)
    elif action == "show":
        return _cmd_account_show(olivos_config, args)

    return 0


def _cmd_account_list(config: OlivOSConfigManager) -> int:
    """列出所有账号"""
    accounts = config.list_accounts()

    from rich.console import Console
    from rich.table import Table

    console = logger.console

    if not accounts:
        console.print("[yellow]暂无账号配置[/yellow]")
        return 0

    table = Table(title="账号列表")
    table.add_column("ID", style="cyan")
    table.add_column("适配器", style="green")
    table.add_column("平台", style="blue")
    table.add_column("模型", style="yellow")

    for acc in accounts:
        table.add_row(str(acc.id), acc.sdk_type, acc.platform_type, acc.model_type)

    console.print(table)
    return 0


def _cmd_account_add(config: OlivOSConfigManager, args) -> int:
    """添加账号"""
    # 尝试从 OlivOS 读取预配置的账号类型
    try:
        from ...olivos import get_account_api
        account_api = get_account_api(config.root_path)

        # 选择账号类型（传入 account_api 以获取完整数据）
        account_type_config = _select_account_type(account_api, args)
        if account_type_config:
            # 使用预配置的账号类型
            return _add_account_with_type(config, account_type_config, args)
    except Exception as e:
        logger.debug(f"无法读取 OlivOS 账号类型配置: {e}")

    # 回退到原来的选择方式
    return _add_account_legacy(config, args)


def _select_account_type(account_api, args) -> dict | None:
    """选择预配置的账号类型

    选择流程:
    1. 从 accountTypeDataList_platform 读取平台列表
    2. 用户选择平台
    3. 从 accountTypeMappingList 筛选该平台的账号类型模板
    4. 用户选择模板（或自定义）
    """
    # 获取平台列表
    platform_list = account_api.get_platform_list()
    if not platform_list:
        logger.warning_print("无法读取平台列表")
        return None

    # 获取所有账号类型配置
    account_types = account_api.get_account_types()
    if not account_types:
        logger.warning_print("无法读取账号类型配置")
        return None

    # 非交互模式直接返回
    if args.non_interactive:
        logger.error_print("非交互模式需要使用 --adapter 指定适配器")
        return None

    # 平台名称映射
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

    # 步骤 1: 选择平台
    platform_choices = [platform_names.get(p, p) for p in platform_list]
    platform_choice = select("选择平台", platform_choices)
    platform_idx = platform_choices.index(platform_choice)
    selected_platform = platform_list[platform_idx]

    # 步骤 2: 筛选该平台的账号类型模板
    platform_templates = []
    for name, cfg in account_types.items():
        if cfg.platform == selected_platform:
            platform_templates.append((name, cfg))

    if not platform_templates:
        logger.warning_print(f"平台 {platform_names.get(selected_platform, selected_platform)} 没有可用的账号类型模板")
        return None

    # 步骤 3: 显示账号类型模板列表
    template_choices = []
    for name, cfg in platform_templates:
        template_choices.append(f"{name}")

    # 添加"自定义"选项
    template_choices.append("自定义配置")

    template_choice = select("选择账号类型模板", template_choices)
    template_idx = template_choices.index(template_choice)

    # 检查是否选择"自定义"
    if template_idx == len(template_choices) - 1:
        logger.info_print("已选择: 自定义配置")
        # 返回 None 让用户使用 legacy 方式自定义
        return None

    # 获取选择的模板
    selected_name, selected_template = platform_templates[template_idx]

    logger.info_print(f"已选择: {selected_template.name}")
    logger.info_print(f"  平台: {selected_template.platform}")
    logger.info_print(f"  SDK: {selected_template.sdk}")
    logger.info_print(f"  模型: {selected_template.model}")

    # 添加提示信息
    _print_platform_tips(selected_template.platform)

    return {
        "platform": selected_template.platform,
        "sdk": selected_template.sdk,
        "model": selected_template.model,
        "server_auto": selected_template.server_auto,
        "server_type": selected_template.server_type,
    }


def _add_account_with_type(config: OlivOSConfigManager, type_config: dict, args) -> int:
    """使用预配置类型添加账号"""
    from ...models import AccountServer

    # 收集账号 ID
    account_data = {}
    if args.id:
        account_data["id"] = args.id
    elif args.non_interactive:
        logger.error_print("非交互模式需要指定 --id 参数")
        return 1
    else:
        while True:
            id_input = ask("账号 ID")
            if id_input and id_input.strip():
                account_data["id"] = id_input.strip()
                break
            logger.error_print("账号 ID 不能为空")

    # 收集密码（如果需要）
    password = ""
    if args.token:
        password = args.token
    elif not args.non_interactive:
        # Hack.Chat 需要房间名称作为 ID，Bot 名称作为密码
        if type_config["platform"] == "hackChat":
            password = ask("Bot 名称", password=True)
        elif type_config["platform"] in ["qq", "wechat"]:
            password = ask("密码/Token", password=True)
        # 米游社大别野也需要密码
        elif type_config["platform"] == "mhyVila":
            password = ask("密码", password=True)

    # 收集服务器配置
    server_data = AccountServer(
        auto=type_config["server_auto"],
        type=type_config["server_type"],
        host="",
        port=0,
        access_token="",
    )

    # 询问访问令牌（如果需要）
    if not args.non_interactive:
        # 检查是否需要访问令牌
        # 需要访问令牌的平台列表
        token_requiring_platforms = [
            "telegram",      # Telegram Bot
            "qqGuild",       # QQ 频道 V1/V2
            "discord",       # Discord Bot
            "kaiheila",      # KOOK
            "biliLive",      # B站直播间
            "mhyVila",       # 米游社大别野
            "dodo",          # Dodo
            "fanbook",       # Fanbook
            "hackChat",      # Hack.Chat
            "xiaoheihe",     # 小黑盒
        ]

        if type_config["platform"] in token_requiring_platforms:
            # 根据平台显示不同的提示信息
            if type_config["platform"] == "telegram":
                token_name = "Bot Token (来自 @botfather)"
            elif type_config["platform"] == "biliLive":
                token_name = "访问令牌（登录模式需要）"
            else:
                token_name = "访问令牌"

            access_token = ask(f"{token_name}", password=True)
            if access_token:
                server_data.access_token = access_token

    # 如果不是自动模式，询问服务器配置
    if not type_config["server_auto"] and not args.non_interactive:
        if type_config["server_type"] == "websocket":
            host = ask("服务器地址", default="127.0.0.1")
            port = int(ask("服务器端口", default="5700"))
            server_data.host = host
            server_data.port = port

    # 创建账号
    account = Account(
        id=account_data["id"],
        password=password,
        sdk_type=type_config["sdk"],
        platform_type=type_config["platform"],
        model_type=type_config["model"],
        debug=getattr(args, 'debug', False),
        server=server_data,
        extends={},
    )

    # 验证
    from ...core.validation import validate_account_config

    validation = validate_account_config(account.to_dict(), None)
    if not validation.valid:
        logger.error_print("账号配置验证失败:")
        for err in validation.errors:
            logger.console.print(f"  - {err}", style="red")
        if validation.warnings:
            logger.warning_print("警告:")
            for warn in validation.warnings:
                logger.console.print(f"  - {warn}", style="yellow")
        return 1

    if validation.warnings:
        logger.warning_print("警告:")
        for warn in validation.warnings:
            logger.console.print(f"  - {warn}", style="yellow")

        if not confirm("仍有警告，是否继续？"):
            return 1

    # 添加
    try:
        config.add_account(account)
        return 0
    except OlivOSConfigError as e:
        logger.error_print(str(e))
        return 1


def _add_account_legacy(config: OlivOSConfigManager, args) -> int:
    """使用原来的方式添加账号"""
    # 选择适配器
    adapter_key = _select_adapter(args)
    if not adapter_key:
        return 1

    adapter = get_adapter_config(adapter_key)

    # 选择 model_type（如果有多个选项）
    model_type = _select_model_type(adapter, args)
    if model_type:
        adapter.model_type = model_type

    # 收集账号信息
    account_data = _collect_account_info(adapter, args)

    # 收集服务器配置
    server_data = _collect_server_info(adapter, args)

    # 收集扩展字段
    extends_data = _collect_extends_info(adapter, args)

    # 创建账号
    account = Account(
        id=account_data["id"],
        password=account_data.get("password", ""),
        sdk_type=adapter.sdk_type,
        platform_type=adapter.platform_type,
        model_type=adapter.model_type,
        debug=getattr(args, 'debug', False),
        server=server_data,
        extends=extends_data,
    )

    # 验证
    from ...core.validation import validate_account_config

    validation = validate_account_config(account.to_dict(), adapter_key)
    if not validation.valid:
        logger.error_print("账号配置验证失败:")
        for err in validation.errors:
            logger.console.print(f"  - {err}", style="red")
        if validation.warnings:
            logger.warning_print("警告:")
            for warn in validation.warnings:
                logger.console.print(f"  - {warn}", style="yellow")
        return 1

    if validation.warnings:
        logger.warning_print("警告:")
        for warn in validation.warnings:
            logger.console.print(f"  - {warn}", style="yellow")

        if not confirm("仍有警告，是否继续？"):
            return 1

    # 添加
    try:
        config.add_account(account)
        return 0
    except OlivOSConfigError as e:
        logger.error_print(str(e))
        return 1


def _select_adapter(args) -> str | None:
    """选择适配器"""
    if args.adapter:
        adapter_key = args.adapter
        # 检查适配器是否存在
        if get_adapter_config(adapter_key):
            return adapter_key
        else:
            logger.error_print(f"不支持的适配器: {adapter_key}")
            _list_available_adapters()
            return None
    elif args.non_interactive:
        logger.error_print("非交互模式需要指定 --adapter 参数")
        return None

    # 交互式选择
    return _interactive_select_adapter()


def _interactive_select_adapter() -> str | None:
    """交互式选择适配器"""
    from ...core import ALL_ADAPTERS

    # 列出所有适配器
    adapters = []
    for key, cfg in ALL_ADAPTERS.items():
        adapters.append((key, cfg))

    if not adapters:
        logger.error_print("没有可用适配器")
        return None

    # 选择具体适���器
    adapter_choices = []
    for key, cfg in adapters:
        desc = f"{cfg.name}"
        if cfg.description:
            desc += f" - {cfg.description}"
        adapter_choices.append(desc)

    # select 返回选择的值，需要找到对应索引
    selected = select("选择适配器", adapter_choices)
    idx = adapter_choices.index(selected)

    selected_key, selected_adapter = adapters[idx]
    logger.info_print(f"已选择: {selected_adapter.name}")
    if selected_adapter.help_text:
        logger.info_print(f"  {selected_adapter.help_text}")

    return selected_key


def _list_available_adapters():
    """列出所有可用适配器"""
    from rich.console import Console
    from rich.table import Table
    from ...core import ALL_ADAPTERS

    console = logger.console

    table = Table(title="可用适配器")
    table.add_column("键", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("描述", style="blue")

    for key, adapter in ALL_ADAPTERS.items():
        table.add_row(key, adapter.name, adapter.description)

    console.print(table)
    logger.info_print("使用适配器键作为 --adapter 参数")


def _select_model_type(adapter, args) -> str | None:
    """选择 model_type"""
    if not adapter.model_type_options:
        return adapter.model_type

    model_type = getattr(args, 'model_type', None)
    if model_type:
        if model_type in adapter.model_type_options:
            return model_type
        else:
            logger.error_print(f"无效的 model_type: {model_type}")
            logger.info_print(f"可用选项: {', '.join(adapter.model_type_options.keys())}")
            return None

    if args.non_interactive:
        return adapter.model_type

    # 交互式选择
    options = list(adapter.model_type_options.items())
    choices = [f"{name} - {desc}" for name, desc in options]
    selected = select("选择模型类型", choices)
    idx = choices.index(selected)
    return options[idx][0]


def _collect_account_info(adapter, args) -> dict:
    """收集账号基本信息"""
    info = {}

    # id - 所有适配器都需要 ID
    if args.id:
        info["id"] = args.id
    elif args.non_interactive:
        raise ValueError("非交互模式需要指定 --id 参数")
    else:
        # 持续询问直到获得有效输入
        while True:
            id_input = ask("账号 ID")
            if id_input and id_input.strip():
                info["id"] = id_input.strip()
                break
            logger.error_print("账号 ID 不能为空")

    # password
    if "password" in adapter.required_fields or "password" in adapter.optional_fields:
        if args.token:
            info["password"] = args.token
        elif args.non_interactive:
            info["password"] = ""
        else:
            info["password"] = ask("密码/Token", password=True)

    # access_token (某些适配器需要)
    if "server.access_token" in adapter.required_fields:
        access_token = getattr(args, 'access_token', None)
        if access_token:
            info["access_token"] = access_token
        elif args.non_interactive:
            info["access_token"] = ""
        else:
            info["access_token"] = ask("访问令牌 (access_token)", password=True)

    return info


def _collect_server_info(adapter, args) -> AccountServer:
    """收集服务器配置"""
    server_args = {}

    # URL 优先
    url = getattr(args, 'url', None)
    if url:
        return AccountServer(
            auto=adapter.server_auto,
            type=adapter.server_type.value,
            url=url,
            access_token=getattr(args, 'access_token', "") or "",
        )

    # host 和 port
    host = args.host
    port = args.port
    access_token = getattr(args, 'access_token', None)

    # 交互式询问
    if not adapter.server_auto and not host:
        if not args.non_interactive:
            host = ask("服务器地址", default="127.0.0.1")

    if not adapter.server_auto and not port:
        if not args.non_interactive:
            port = int(ask("服务器端口", default="5700"))

    return AccountServer(
        auto=adapter.server_auto,
        type=adapter.server_type.value,
        host=host or "",
        port=port or 0,
        access_token=access_token or "",
    )


def _collect_extends_info(adapter, args) -> dict:
    """收集扩展字段"""
    if not adapter.extends_options:
        return {}

    extends = {}

    # 从命令行参数解析 --extends key=value 格式
    extends_args = getattr(args, 'extends', None)
    if extends_args:
        for item in extends_args:
            if "=" in item:
                key, value = item.split("=", 1)
                extends[key] = value
            else:
                logger.warning_print(f"忽略无效的扩展字段: {item}")

    # 交互式询问未提供的必填扩展字段
    if not args.non_interactive:
        for key, options in adapter.extends_options.items():
            if key not in extends:
                value = ask(f"扩展字段 {key} ({options.get('description', '')})")
                extends[key] = value

    return extends


def _cmd_account_remove(config: OlivOSConfigManager, args) -> int:
    """删除账号"""
    account_id = args.account_id

    # 确认
    if not confirm(f"确定要删除账号 {account_id} 吗？"):
        return 0

    if config.remove_account(account_id):
        logger.success(f"账号已删除: {account_id}")
        return 0
    else:
        logger.error_print(f"账号不存在: {account_id}")
        return 1


def _cmd_account_show(config: OlivOSConfigManager, args) -> int:
    """显示账号详情"""
    account = config.get_account(args.account_id)

    if not account:
        logger.error_print(f"账号不存在: {args.account_id}")
        return 1

    from rich.console import Console
    from rich.table import Table

    console = logger.console

    table = Table(title=f"账号详情: {args.account_id}")
    table.add_column("项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("ID", str(account.id))
    table.add_row("SDK 类型", account.sdk_type)
    table.add_row("平台类型", account.platform_type)
    table.add_row("模型类型", account.model_type)
    table.add_row("调试模式", "是" if account.debug else "否")

    if account.server:
        table.add_row("服务器类型", account.server.type)
        if account.server.host:
            table.add_row("服务器地址", f"{account.server.host}:{account.server.port}")
        if account.server.url:
            table.add_row("服务器URL", account.server.url)
        if account.server.access_token:
            token = account.server.access_token
            table.add_row("访问令牌", f"**{token[-4:]}")

    if account.extends:
        table.add_row("扩展字段", str(account.extends))

    console.print(table)
    return 0


def _print_platform_tips(platform: str):
    """打印平台的配置提示信息"""
    tips = {
        "telegram": [
            "💡 Telegram 配置提示：",
            "  • 账号 ID：机器人的用户名或数字 ID",
            "  • Bot Token：通过 @Botfather 创建机器人时获得",
            "  • 格式示例：123456789:AAH4XXX..."
        ],
        "qqGuild": [
            "💡 QQ 频道配置提示：",
            "  • 账号 ID：频道的 ID",
            "  • 访问令牌：从 QQ 频道开放平台获取"
        ],
        "discord": [
            "💡 Discord 配置提示：",
            "  • 账号 ID：机器人的客户端 ID（可选）",
            "  • 访问令牌：从 Discord 开发者平台获取"
        ],
        "kaiheila": [
            "💡 KOOK 配置提示：",
            "  • 访问令牌：从 KOOK 开放平台获取"
        ],
        "biliLive": [
            "💡 B站直播间配置提示：",
            "  • 访问令牌：登录模式需要，从 B站获取"
        ],
        "mhyVila": [
            "💡 米游社大别野配置提示：",
            "  • 账号 ID：用户 ID",
            "  • 密码：用户密码",
            "  • 访问令牌：从米游社获取"
        ],
        "dodo": [
            "💡 Dodo 配置提示：",
            "  • 账号 ID：Bot ID",
            "  • 访问令牌：从 Dodo 开放平台获取"
        ],
        "fanbook": [
            "💡 Fanbook 配置提示：",
            "  • 访问令牌：从 Fanbook 开放平台获取"
        ],
        "hackChat": [
            "💡 Hack.Chat 配置提示：",
            "  • 账号 ID：房间名称",
            "  • Bot 名称：机器人的名称",
            "  • 访问令牌：Bot 名称（再次输入）"
        ],
        "xiaoheihe": [
            "💡 小黑盒配置提示：",
            "  • 访问令牌：从小黑盒开放平台获取"
        ]
    }

    if platform in tips:
        for tip in tips[platform]:
            logger.info_print(f"  {tip}")
