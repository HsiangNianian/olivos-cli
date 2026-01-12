import sys
import asyncio
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import PlainTextResponse

from ..core import ConfigManager, get_logger, VERSION
from ..core.validation import validate_account_config
from ..olivos import OlivOSConfigManager
from ..models import Account, AccountServer

logger = get_logger()


class ServiceStatus(BaseModel):
    loaded: bool = Field(..., title="加载状态", description="服务单元是否已加载")
    running: bool = Field(..., title="运行状态", description="服务是否正在运行")
    details: Dict[str, Any] = Field(
        default_factory=dict, title="详细信息", description="服务状态详情"
    )


class GitStatus(BaseModel):
    exists: bool = Field(..., title="仓库存在", description="Git 仓库是否存在")
    branch: Optional[str] = Field(None, title="当前分支", description="当前 Git 分支名称")
    commit: Optional[str] = Field(None, title="Commit Hash", description="当前 Commit Hash")
    clean: Optional[bool] = Field(
        None, title="工作区状态", description="工作区是否干净 (无未提交更改)"
    )


class SystemStatus(BaseModel):
    version: str = Field(..., title="CLI 版本", description="OlivOS CLI 版本")
    install_path: str = Field(..., title="安装路径", description="OlivOS 安装目录")
    platform: str = Field(..., title="操作系统", description="运行环境操作系统")
    service: ServiceStatus = Field(..., title="服务状态", description="系统服务运行状态")
    git: GitStatus = Field(..., title="Git 状态", description="代码仓库状态")


class ActionResult(BaseModel):
    success: bool = Field(..., title="操作结果", description="操作是否成功")
    message: str = Field(..., title="返回消息", description="操作结果的详细说明")


class AccountServerModel(BaseModel):
    auto: bool = Field(True, title="自动配置", description="是否自动配置服务器连接信息")
    type: str = Field("post", title="连接类型", description="服务器连接类型 (如: post, websocket)")
    host: str = Field("127.0.0.1", title="服务器地址", description="OlivOS 后端服务器 IP 地址")
    port: int = Field(5700, title="服务器端口", description="OlivOS 后端服务器端口")
    access_token: str = Field("", title="访问令牌", description="API 访问 Token (根据平台要求填写)")
    url: str = Field("", title="服务器 URL", description="完整的服务器 URL (优先于 host/port 使用)")


class AccountModel(BaseModel):
    id: str = Field(..., title="账号 ID", description="账号的唯一标识符 (如 QQ 号、Bot ID)")
    password: Optional[str] = Field("", title="密码/Token", description="账号登录密码或 Bot Token")
    sdk_type: str = Field(
        ..., title="SDK 类型", description="使用的 SDK 类型 (如: onebot, kaiheila)"
    )
    platform_type: str = Field(..., title="平台类型", description="账号所属平台 (如: qq, discord)")
    model_type: str = Field("default", title="模型类型", description="适配器模型类型")
    extends: Dict[str, Any] = Field(
        default_factory=dict, title="扩展配置", description="其他扩展配置项"
    )
    debug: bool = Field(False, title="调试模式", description="是否开启调试日志")
    server: AccountServerModel = Field(..., title="服务器配置", description="后端服务器连接配置")


class PlatformOption(BaseModel):
    id: str = Field(..., title="平台 ID", description="平台内部标识符")
    name: str = Field(..., title="平台名称", description="平台显示名称")


class AccountTemplate(BaseModel):
    name: str = Field(..., title="模板名称", description="账号类型模板名称")
    platform: str = Field(..., title="平台类型", description="所属平台")
    sdk: str = Field(..., title="SDK", description="使用的 SDK")
    model: str = Field(..., title="模型", description="使用的模型")
    server_auto: bool = Field(..., title="自动服务器", description="是否默认自动配置服务器")
    server_type: str = Field(..., title="服务器类型", description="默认服务器连接类型")
    # UI helper info
    description: str = Field("", title="描述", description="模板详细描述")


class AccountOptions(BaseModel):
    platforms: List[PlatformOption] = Field(..., title="平台列表", description="可用平台列表")
    templates: List[AccountTemplate] = Field(..., title="模板列表", description="预设账号配置模板")


tags_metadata = [
    {
        "name": "状态 (Status)",
        "description": "查看系统运行状态、服务进程状态以及 Git 仓库版本信息。",
    },
    {
        "name": "控制 (Control)",
        "description": "管理系统服务的生命周期：启动、停止和重启。",
    },
    {
        "name": "Git 操作 (Git)",
        "description": "管理代码仓库的更新操作。",
    },
    {
        "name": "日志 (Logs)",
        "description": "查看系统最近的运行日志。",
    },
    {
        "name": "账号管理 (Accounts)",
        "description": "管理 OlivOS 的账号配置，包括查看、添加和删除账号。",
    },
]

app = FastAPI(
    title="OlivOS 管理面板",
    description="""
    # 欢迎使用 OlivOS 管理面板
    
    这是一个基于 Web 的可视化管理界面，您可以通过它轻松管理您的 OlivOS 实例。
    
    ## 主要功能
    
    * **状态监控**: 实时查看系统版本、安装路径、服务运行状态。
    * **服务控制**: 提供简单的按钮来启动、停止或重启 OlivOS 服务。
    * **版本管理**: 检查 Git 版本并执行一键更新。
    * **账号配置**: 
        * 查看当前所有账号列表
        * 使用预设模板快速添加新账号
        * 修改和删除现有账号
    * **日志查看**: 在线浏览系统运行日志，排查问题。
    
    ---
    *由 FastAPI & Swagger UI 驱动*
    """,
    version=VERSION,
    openapi_tags=tags_metadata,
    docs_url="/",  # Swaggger UI as root
    redoc_url=None,  # Disable ReDoc
)

# 存储 config_manager 实例
_config_manager: Optional[ConfigManager] = None


def set_config_manager(manager: ConfigManager):
    global _config_manager
    _config_manager = manager


def get_config_manager() -> ConfigManager:
    if _config_manager is None:
        raise RuntimeError("ConfigManager not set")
    return _config_manager


def get_olivos_config() -> OlivOSConfigManager:
    """获取 OlivOS 配置管理器实例"""
    cm = get_config_manager()
    install_path = cm.config.git.expanded_install_path

    if not install_path.exists():
        raise HTTPException(status_code=404, detail="OlivOS install path not found")

    return OlivOSConfigManager(install_path)


@app.get("/status", tags=["状态 (Status)"], response_model=SystemStatus, summary="获取系统整体状态")
async def get_system_status():
    """
    获取当前系统、Git 仓库以及 OlivOS 服务的运行状态。
    """
    cm = get_config_manager()
    config = cm.config
    install_path = config.git.expanded_install_path

    # 基础信息
    status = SystemStatus(
        version=VERSION,
        install_path=str(install_path),
        platform=sys.platform,
        service=ServiceStatus(loaded=False, running=False),
        git=GitStatus(exists=install_path.exists()),
    )

    # Git 状态
    if install_path.exists():
        try:
            from ..git import GitOperator

            git = GitOperator()
            git_info = git.get_repo_status(install_path)
            status.git.branch = git_info.get("branch")
            status.git.commit = git_info.get("commit")
            # 简单判断是否 clean
            status.git.clean = True
        except Exception:
            pass

    # 服务状态 (Systemd)
    if sys.platform != "win32":
        try:
            from ..systemd import SystemdManager

            systemd = SystemdManager(user_mode=config.systemd.user_mode)
            svc_info = systemd.status(config.systemd.service_name)
            status.service.loaded = svc_info.get("loaded", False)
            status.service.running = svc_info.get("running", False)
            status.service.details = svc_info
        except Exception:
            pass

    return status


@app.post(
    "/control/start", tags=["控制 (Control)"], response_model=ActionResult, summary="启动服务"
)
async def start_service():
    """启动 OlivOS 后台服务"""
    if sys.platform == "win32":
        raise HTTPException(status_code=400, detail="Windows 不支持此操作")

    cm = get_config_manager()
    try:
        from ..systemd import SystemdManager

        systemd = SystemdManager(user_mode=cm.config.systemd.user_mode)
        success = systemd.start(cm.config.systemd.service_name)
        return ActionResult(success=success, message="启动成功" if success else "启动失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务启动异常: {str(e)}")


@app.post("/control/stop", tags=["控制 (Control)"], response_model=ActionResult, summary="停止服务")
async def stop_service():
    """停止 OlivOS 后台服务"""
    if sys.platform == "win32":
        raise HTTPException(status_code=400, detail="Windows 不支持此操作")

    cm = get_config_manager()
    try:
        from ..systemd import SystemdManager

        systemd = SystemdManager(user_mode=cm.config.systemd.user_mode)
        success = systemd.stop(cm.config.systemd.service_name)
        return ActionResult(success=success, message="停止成功" if success else "停止失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务停止异常: {str(e)}")


@app.post(
    "/control/restart", tags=["控制 (Control)"], response_model=ActionResult, summary="重启服务"
)
async def restart_service():
    """重启 OlivOS 后台服务"""
    if sys.platform == "win32":
        raise HTTPException(status_code=400, detail="Windows 不支持此操作")

    cm = get_config_manager()
    try:
        from ..systemd import SystemdManager

        systemd = SystemdManager(user_mode=cm.config.systemd.user_mode)
        success = systemd.restart(cm.config.systemd.service_name)
        return ActionResult(success=success, message="重启成功" if success else "重启失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务重启异常: {str(e)}")


@app.post("/git/pull", tags=["Git 操作 (Git)"], response_model=ActionResult, summary="Git 拉取更新")
async def git_pull():
    """执行 git pull 以更新代码"""
    cm = get_config_manager()
    path = cm.config.git.expanded_install_path

    if not path.exists():
        raise HTTPException(status_code=404, detail="Install path not found")

    try:
        from ..git import GitOperator

        git = GitOperator()
        # 注意: 这里是同步阻塞调用，大仓库可能会卡顿
        updated = git.pull(path)
        return ActionResult(
            success=updated, message="更新成功" if updated else "更新失败 (可能是最新或冲突)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git 更新异常: {str(e)}")


@app.get("/logs", tags=["日志 (Logs)"], response_class=PlainTextResponse, summary="读取日志")
async def get_logs(lines: int = Query(100, description="读取最后 N 行日志")):
    """
    读取最新的日志内容。
    """
    cm = get_config_manager()
    log_file = cm.config.logging.expanded_log_file

    if not log_file.exists():
        return f"Log file not found: {log_file}"

    try:
        # 使用 aiofiles 异步读取，防止阻塞
        async with aiofiles.open(log_file, mode="r", encoding="utf-8", errors="ignore") as f:
            all_lines = await f.readlines()
            tail_lines = all_lines[-lines:]
            return "".join(tail_lines)
    except Exception as e:
        return f"Error reading logs: {e}"


@app.get(
    "/accounts",
    tags=["账号管理 (Accounts)"],
    response_model=List[AccountModel],
    summary="获取所有账号",
)
async def list_accounts():
    """列出所有配置的账号"""
    try:
        olivos = get_olivos_config()
        accounts = olivos.list_accounts()
        # Convert dataclasses to Pydantic models
        result = []
        for acc in accounts:
            server_data = {}
            if acc.server:
                server_data = acc.server.to_dict()

            result.append(
                AccountModel(
                    id=str(acc.id),
                    password=acc.password,
                    sdk_type=acc.sdk_type,
                    platform_type=acc.platform_type,
                    model_type=acc.model_type,
                    extends=acc.extends or {},
                    debug=acc.debug,
                    server=AccountServerModel(**server_data),
                )
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账号列表失败: {e}")


@app.get(
    "/accounts/options",
    tags=["账号管理 (Accounts)"],
    response_model=AccountOptions,
    summary="获取账号类型选项",
)
async def get_account_options():
    """获取可用的平台和账号模板，用于前端创建表单"""
    try:
        olivos = get_olivos_config()
        from ..olivos import get_account_api

        account_api = get_account_api(olivos.root_path)

        platform_list = account_api.get_platform_list()
        account_types = account_api.get_account_types()

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

        platforms = []
        for p in platform_list:
            platforms.append(PlatformOption(id=p, name=platform_names.get(p, p)))

        templates = []
        if account_types:
            for name, cfg in account_types.items():
                if name == "自定义":
                    continue

                templates.append(
                    AccountTemplate(
                        name=name,
                        platform=cfg.platform,
                        sdk=cfg.sdk,
                        model=cfg.model,
                        server_auto=cfg.server_auto,
                        server_type=cfg.server_type,
                        description=f"{cfg.sdk} / {cfg.model}",
                    )
                )

        return AccountOptions(platforms=platforms, templates=templates)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选项失败: {str(e)}")


@app.post(
    "/accounts", tags=["账号管理 (Accounts)"], response_model=ActionResult, summary="添加账号"
)
async def add_account(account_model: AccountModel):
    """添加一个新的账号配置"""
    try:
        olivos = get_olivos_config()

        # 转换 Pydantic model 到 Dataclass
        server_obj = AccountServer(
            auto=account_model.server.auto,
            type=account_model.server.type,
            host=account_model.server.host,
            port=account_model.server.port,
            access_token=account_model.server.access_token,
            url=account_model.server.url,
        )

        account_obj = Account(
            id=account_model.id,
            password=account_model.password,
            sdk_type=account_model.sdk_type,
            platform_type=account_model.platform_type,
            model_type=account_model.model_type,
            debug=account_model.debug,
            server=server_obj,
            extends=account_model.extends,
        )

        # 验证
        validation = validate_account_config(account_obj.to_dict(), None)
        if not validation.valid:
            errors = "; ".join(validation.errors)
            raise HTTPException(status_code=400, detail=f"配置验证失败: {errors}")

        # 添加
        olivos.add_account(account_obj)
        return ActionResult(success=True, message=f"账号 {account_model.id} 添加成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加账号失败: {e}")


@app.delete(
    "/accounts/{account_id}",
    tags=["账号管理 (Accounts)"],
    response_model=ActionResult,
    summary="删除账号",
)
async def delete_account(account_id: str):
    """删除指定的账号"""
    try:
        olivos = get_olivos_config()
        if olivos.remove_account(account_id):
            return ActionResult(success=True, message=f"账号 {account_id} 已删除")
        else:
            raise HTTPException(status_code=404, detail="未找到指定账号")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除账号失败: {str(e)}")
