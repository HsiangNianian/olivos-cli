import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm
from rich.table import Table

console = Console()

REPO_URL = "https://github.com/OlivOS-Team/OlivOS.git"
REPO_DIR_NAME = "OlivOS"


def _clone_olivos(force: bool = False, auto_confirm: bool = False) -> bool:
    target_dir = Path.cwd() / REPO_DIR_NAME

    if target_dir.exists():
        if not force:
            if not auto_confirm:
                overwrite = Confirm.ask(
                    f"检测到 [bold]{REPO_DIR_NAME}[/bold] 目录，是否覆盖?",
                    default=False,
                )
                if not overwrite:
                    console.print("[yellow]已保留现有目录，跳过拉取。[/yellow]")
                    return False
        try:
            shutil.rmtree(target_dir)
        except Exception as exc:
            console.print(f"[bold red]无法删除现有目录：{exc}[/bold red]")
            return False

    output_lines: list[str] = []
    with console.status("[bold cyan]正在拉取 OlivOS 仓库...[/bold cyan]") as status:
        process = subprocess.Popen(
            ["git", "clone", REPO_URL, REPO_DIR_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if process.stdout:
            for line in process.stdout:
                output_lines.append(line)
                status.console.print(
                    line.rstrip(),
                    style="grey58",
                    markup=False,
                    highlight=False,
                )

        return_code = process.wait()

    if return_code == 0:
        console.print("[bold green]✓ 拉取成功[/bold green]")
        return True

    console.print("[bold red]✗ 拉取失败[/bold red]")
    if output_lines:
        console.print(
            "".join(output_lines),
            style="grey58",
            markup=False,
            highlight=False,
        )
    return False


def cmd_deploy(args):
    """部署 OlivOS 应用：可选地拉取仓库，然后安装依赖"""

    olivos_dir = Path.cwd() / REPO_DIR_NAME

    if not olivos_dir.exists():
        console.print("[cyan]检测到本地缺少 OlivOS 仓库，正在拉取...[/cyan]")
        if not _clone_olivos(force=True, auto_confirm=True):
            console.print(Panel("[bold red]✗ 部署失败：仓库拉取失败[/bold red]"))
            return
    elif args.yes:
        console.print("[cyan]根据 --yes 参数，重新拉取 OlivOS 仓库...[/cyan]")
        if not _clone_olivos(force=True, auto_confirm=True):
            console.print(Panel("[bold red]✗ 部署失败：仓库拉取失败[/bold red]"))
            return
    else:
        console.print(
            "[yellow]已存在 OlivOS 目录，跳过拉取。（使用 --yes 可强制更新）[/yellow]"
        )

    requirements_file = olivos_dir / (
        "requirements310_win.txt"
        if platform.system() == "Windows"
        else "requirements310.txt"
    )
    if not requirements_file.exists():
        console.print(
            Panel(f"[bold red]✗ 未找到依赖文件：{requirements_file}[/bold red]")
        )
        return

    console.print(Panel(f"[bold cyan]安装依赖：{requirements_file.name}[/bold cyan]"))
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
    )

    if result.returncode == 0:
        console.print(Panel("[bold green]✓ 部署完成[/bold green]"))
    else:
        console.print(Panel("[bold red]✗ 部署失败：安装依赖出错[/bold red]"))


def cmd_update(args):
    """更新 OlivOS 依赖"""
    console.print("[bold cyan]更新依赖中...[/bold cyan]")

    with Progress() as progress:
        task = progress.add_task("[cyan]获取最新版本...", total=100)

        progress.update(task, advance=40, description="[cyan]下载更新...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "olivos"],
            capture_output=True,
        )
        progress.update(task, advance=100, description="[cyan]更新完成")

    if result.returncode == 0:
        console.print(Panel("[bold green]✓ 依赖更新成功[/bold green]"))
    else:
        console.print(Panel("[bold red]✗ 依赖更新失败[/bold red]"))


def cmd_pull(args):
    """将 OlivOS 仓库克隆到当前目录"""

    force = args.force
    auto_confirm = args.force
    _clone_olivos(force=force, auto_confirm=auto_confirm)


def cmd_run(args):
    """运行当前目录下 OlivOS/main.py"""

    olivos_main = Path.cwd() / REPO_DIR_NAME / "main.py"
    if not olivos_main.exists():
        console.print(
            Panel(
                "[bold red]✗ 未找到 OlivOS/main.py，请先执行 pull 或 deploy[/bold red]"
            )
        )
        return

    console.print(Panel("[bold cyan]运行 OlivOS/main.py...[/bold cyan]"))
    result = subprocess.run([sys.executable, str(olivos_main)], cwd=olivos_main.parent)

    if result.returncode == 0:
        console.print("[bold green]✓ OlivOS 已退出[/bold green]")
    else:
        console.print(
            f"[bold red]✗ OlivOS 运行失败 (退出码 {result.returncode})[/bold red]"
        )


def cmd_config(args):
    """管理配置文件"""
    config_path = Path.home() / ".olivos" / "config.json"

    if args.action == "show":
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)

            table = Table(title="当前配置")
            table.add_column("配置项", style="cyan")
            table.add_column("值", style="green")
            for k, v in config.items():
                table.add_row(k, str(v))
            console.print(table)
        else:
            console.print("[yellow]⚠ 配置文件不存在，请先运行 init[/yellow]")

    elif args.action == "set":
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)

            config[args.key] = args.value

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            console.print(
                Panel(
                    f"[bold green]✓ 配置已更新: {args.key} = {args.value}[/bold green]"
                )
            )
        else:
            console.print("[yellow]⚠ 配置文件不存在[/yellow]")

    elif args.action == "reset":
        default_config = {
            "olivos_path": str(Path.cwd() / "OlivOS"),
            "plugin_dir": str(Path.cwd() / "plugins"),
            "conf_dir": str(Path.cwd() / "conf"),
            "log_level": "INFO",
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        console.print(Panel("[bold green]✓ 配置已重置为默认值[/bold green]"))


def main():
    parser = argparse.ArgumentParser(
        prog="olivos-cli",
        description="OlivOS 命令行工具 - 用于构建、部署和管理 OlivOS 应用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  olivos-cli build\n  olivos-cli init\n  olivos-cli run\n  olivos-cli config show",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用的子命令")

    # deploy 命令
    parser_deploy = subparsers.add_parser("deploy", help="拉取仓库并安装依赖")
    parser_deploy.add_argument(
        "-y", "--yes", action="store_true", help="跳过仓库覆盖确认，强制重新拉取"
    )
    parser_deploy.set_defaults(func=cmd_deploy)

    # update 命令
    parser_update = subparsers.add_parser("update", help="更新 OlivOS 依赖")
    parser_update.set_defaults(func=cmd_update)

    # pull 命令
    parser_pull = subparsers.add_parser("pull", help="从官方仓库拉取 OlivOS")
    parser_pull.add_argument(
        "-f", "--force", action="store_true", help="强制覆盖现有 OlivOS 目录"
    )
    parser_pull.set_defaults(func=cmd_pull)

    # run 命令
    parser_run = subparsers.add_parser("run", help="运行 OlivOS 服务")
    parser_run.set_defaults(func=cmd_run)

    # config 命令
    parser_config = subparsers.add_parser("config", help="管理配置文件")
    config_subparsers = parser_config.add_subparsers(dest="action")

    parser_config_show = config_subparsers.add_parser("show", help="显示当前配置")
    parser_config_show.set_defaults(func=cmd_config)

    parser_config_set = config_subparsers.add_parser("set", help="设置配置项")
    parser_config_set.add_argument("key", help="配置项名")
    parser_config_set.add_argument("value", help="配置项值")
    parser_config_set.set_defaults(func=cmd_config)

    parser_config_reset = config_subparsers.add_parser("reset", help="重置配置为默认值")
    parser_config_reset.set_defaults(func=cmd_config)

    # 解析参数
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
