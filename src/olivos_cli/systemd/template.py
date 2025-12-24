# -*- coding: utf-8 -*-
"""
systemd service 模板生成
使用 Jinja2 渲染模板
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    # 回退到简单字符串替换
    Environment = None

from ..core import get_logger

logger = get_logger()


@dataclass
class ServiceTemplateData:
    """service 模板数据"""

    instance_name: str = "olivos"
    description: str = "OlivOS Bot Framework"
    user: str = ""
    group: str = ""
    working_directory: str = ""
    python_executable: str = "python3"
    main_script: str = "main.py"
    restart_command: Optional[str] = None
    restart_policy: str = "on-failure"
    restart_sec: int = 10
    restrict_address_families: list[str] = None
    private_tmp: bool = True
    no_new_privileges: bool = True
    memory_limit: Optional[str] = None
    cpu_quota: Optional[str] = None
    log_file: str = ""
    error_log_file: str = ""
    timeout_start_sec: int = 30
    timeout_stop_sec: int = 30
    wanted_by: str = "default.target"
    environment: dict[str, str] = None
    depends_on_services: list[str] = None

    def __post_init__(self):
        if self.user == "":
            self.user = os.environ.get("USER", "olivos")
        if self.group == "":
            self.group = self.user
        if self.working_directory == "":
            # 使用当前目录下的 OlivOS
            self.working_directory = str(Path.cwd() / "OlivOS")
        # 日志文件基于工作目录的父目录
        base_dir = Path(self.working_directory).parent
        if self.log_file == "":
            self.log_file = str(base_dir / "logs" / "olivos.log")
        if self.error_log_file == "":
            self.error_log_file = str(base_dir / "logs" / "error.log")
        if self.restrict_address_families is None:
            self.restrict_address_families = ["AF_UNIX", "AF_INET", "AF_INET6"]
        if self.environment is None:
            self.environment = {"PYTHONUNBUFFERED": "1", "OLIVOS_LOG_LEVEL": "INFO"}
        if self.depends_on_services is None:
            # network-online.target 在用户模式下不可用，使用 network.target 即可
            self.depends_on_services = []


# 获取模板目录
def get_template_dir() -> Path:
    """获取模板目录路径"""
    # 尝试从包内获取
    try:
        import olivos_cli as pkg
        pkg_dir = Path(pkg.__file__).parent
        template_dir = pkg_dir / "templates"
        if template_dir.exists():
            return template_dir
    except Exception:
        pass

    # 开发环境
    return Path(__file__).parent.parent.parent.parent / "templates"


def render_service_template(data: ServiceTemplateData) -> str:
    """渲染 service 模板

    Args:
        data: 模板数据

    Returns:
        渲染后的 service 文件内容
    """
    if Environment is not None:
        # 使用 Jinja2
        template_dir = get_template_dir()
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        try:
            template = env.get_template("systemd.service.jinja2")
            return template.render(**data.__dict__)
        except Exception as e:
            logger.warning_print(f"Jinja2 渲染失败: {e}，使用回退方案")

    # 回退方案：简单字符串替换
    return _render_fallback(data)


def _render_fallback(data: ServiceTemplateData) -> str:
    """回退渲染方案"""
    # 处理依赖（用户模式下不使用 network-online.target）
    if data.depends_on_services:
        depends_on = f"Requires={' '.join(data.depends_on_services)}\n"
    else:
        depends_on = ""

    # 处理环境变量
    environment_vars = "\n".join(
        [f'Environment="{k}={v}"' for k, v in data.environment.items()]
    )

    # 处理地址族
    restrict_families = " ".join(data.restrict_address_families)

    # 布尔值转换
    private_tmp = "true" if data.private_tmp else "false"
    no_new_privileges = "true" if data.no_new_privileges else "false"

    # 处理资源限制
    memory_limit = f"MemoryLimit={data.memory_limit}" if data.memory_limit else ""
    cpu_quota = f"CPUQuota={data.cpu_quota}" if data.cpu_quota else ""

    return f"""[Unit]
Description={data.description}
Documentation=https://github.com/OlivOS-Team/OlivOS
After=network.target
{depends_on}

[Service]
Type=simple
User={data.user}
Group={data.group}
WorkingDirectory={data.working_directory}

# 环境变量
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
{environment_vars}

# 启动命令
ExecStart={data.python_executable} {data.main_script}

# 重启策略
Restart={data.restart_policy}
RestartSec={data.restart_sec}

# 安全限制
RestrictAddressFamilies={restrict_families}
PrivateTmp={private_tmp}
NoNewPrivileges={no_new_privileges}
{memory_limit}
{cpu_quota}

# 日志
StandardOutput=append:{data.log_file}
StandardError=append:{data.error_log_file}

# 超时
TimeoutStartSec={data.timeout_start_sec}
TimeoutStopSec={data.timeout_stop_sec}

[Install]
WantedBy={data.wanted_by}
"""


def generate_service_file(
    name: str,
    working_directory: Path,
    output_path: Optional[Path] = None,
    **kwargs,
) -> str:
    """生成 service 文件

    Args:
        name: 服务名称
        working_directory: 工作目录
        output_path: 输出路径 (可选)
        **kwargs: 额外的模板参数

    Returns:
        service 文件内容
    """
    data = ServiceTemplateData(
        instance_name=name,
        working_directory=str(working_directory),
        **kwargs,
    )
    content = render_service_template(data)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
