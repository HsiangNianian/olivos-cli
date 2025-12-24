# -*- coding: utf-8 -*-
import argparse
import sys

from ..core import (
    CONFIG_DIR,
    ConfigManager,
    VERSION,
    get_logger,
)
from ..core.exceptions import OlivOSCLIError

logger = get_logger()


# 命令缩写映射
COMMAND_ALIASES = {
    "i": "init",
    "g": "git",
    "p": "package",
    "pkg": "package",
    "s": "service",
    "svc": "service",
    "a": "adapter",
    "adapt": "adapter",
    "acc": "account",
    "c": "config",
    "cfg": "config",
    "st": "status",
    "v": "version",
    "ver": "version",
    "h": "help",
    "up": "update",
    "ls": "list",
    "co": "checkout",
    "r": "restart",
    "log": "logs",
}

# 子命令缩写映射
SUBCOMMAND_ALIASES = {
    "ls": "list",
    "i": "install",
    "up": "update",
    "st": "status",
    "log": "logs",
    "co": "checkout",
    "r": "restart",
    "rm": "remove",
    "cfg": "config",
}


def resolve_command_alias(cmd: str) -> str:
    """解析命令缩写"""
    return COMMAND_ALIASES.get(cmd, cmd)


def resolve_subcommand_alias(action: str) -> str:
    """解析子命令缩写"""
    return SUBCOMMAND_ALIASES.get(action, action)


class OlivOSCLI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(
            prog="olivos-cli",
            description="OlivOS 命令行工具 - 用于构建、部署和管理 OlivOS 应用",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  olivos-cli init                    初始化安装 OlivOS
  olivos-cli git pull                拉取更新
  olivos-cli package install         安装依赖
  olivos-cli service start           启动服务
  olivos-cli account add             添加账号
  olivos-cli status                  查看状态

命令缩写:
  i/init, g/git, p/pkg/package, s/svc/service
  a/adapt/adapter, acc/account, c/cfg/config
            """,
        )

        parser.add_argument(
            "-v", "--version",
            action="version",
            version=f"olivos-cli {VERSION}",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="详细输出",
        )

        parser.add_argument(
            "--quiet",
            action="store_true",
            help="静默模式",
        )

        parser.add_argument(
            "-y", "--yes",
            action="store_true",
            help="自动确认所有提示",
        )

        parser.add_argument(
            "--config",
            type=str,
            help="指定配置文件路径",
        )

        # 子命令
        subparsers = parser.add_subparsers(
            dest="command",
            help="可用的子命令",
            metavar="COMMAND",
        )

        # init 命令
        self._add_init_parser(subparsers)

        # git 命令
        self._add_git_parser(subparsers)

        # package 命令
        self._add_package_parser(subparsers)

        # service 命令
        self._add_service_parser(subparsers)

        # adapter 命令
        self._add_adapter_parser(subparsers)

        # account 命令
        self._add_account_parser(subparsers)

        # config 命令
        self._add_config_parser(subparsers)

        # logs 命令
        self._add_logs_parser(subparsers)

        # status 命令
        self._add_status_parser(subparsers)

        # run 命令
        self._add_run_parser(subparsers)

        # update 命令
        self._add_update_parser(subparsers)

        return parser

    def _add_init_parser(self, subparsers):
        """添加 init 命令"""
        parser = subparsers.add_parser(
            "init",
            aliases=["i"],
            help="初始化并安装 OlivOS",
        )
        parser.add_argument(
            "--path",
            type=str,
            help="安装路径",
        )
        parser.add_argument(
            "--branch",
            type=str,
            default="main",
            help="Git 分支 (默认: main)",
        )
        parser.add_argument(
            "--mirror",
            action="store_true",
            help="使用镜像源",
        )
        parser.add_argument(
            "--minimal",
            action="store_true",
            help="最小化安装",
        )
        parser.add_argument(
            "--no-deps",
            action="store_true",
            help="跳过依赖安装",
        )
        parser.add_argument(
            "--package-manager", "-p",
            type=str,
            choices=["uv", "pip", "pdm", "poetry", "rye"],
            help="包管理器 (默认: uv)",
        )
        parser.add_argument(
            "--requirements", "-r",
            type=str,
            help="依赖文件路径 (相对于 OlivOS 目录)",
        )

    def _add_git_parser(self, subparsers):
        """添加 git 命令"""
        parser = subparsers.add_parser(
            "git",
            aliases=["g"],
            help="Git 仓库管理",
        )
        git_subparsers = parser.add_subparsers(dest="git_action")

        # clone
        clone_parser = git_subparsers.add_parser("clone", help="克隆仓库")
        clone_parser.add_argument("--branch", type=str, default="main", help="分支名")
        clone_parser.add_argument("--mirror", action="store_true", help="使用镜像源")
        clone_parser.add_argument("-f", "--force", action="store_true", help="强制覆盖")

        # pull
        pull_parser = git_subparsers.add_parser("pull", aliases=["up"], help="拉取更新")
        pull_parser.add_argument("--branch", type=str, help="指定分支")

        # checkout
        co_parser = git_subparsers.add_parser("checkout", aliases=["co"], help="切换分支/提交")
        co_parser.add_argument("ref", help="分支名或 commit hash")

        # status
        git_subparsers.add_parser("status", aliases=["st"], help="查看状态")

    def _add_package_parser(self, subparsers):
        """添加 package 命令"""
        parser = subparsers.add_parser(
            "package",
            aliases=["p", "pkg"],
            help="包管理",
        )
        pkg_subparsers = parser.add_subparsers(dest="pkg_action")

        # install
        install_parser = pkg_subparsers.add_parser("install", aliases=["i"], help="安装依赖")
        install_parser.add_argument(
            "packages",
            nargs="*",
            help="要安装的包 (留空则安装全部依赖)",
        )

        # update
        pkg_subparsers.add_parser("update", aliases=["up"], help="更新依赖")

        # list
        pkg_subparsers.add_parser("list", aliases=["ls"], help="列出已安装的包")

    def _add_service_parser(self, subparsers):
        """添加 service 命令"""
        parser = subparsers.add_parser(
            "service",
            aliases=["s", "svc"],
            help="服务管理",
        )
        svc_subparsers = parser.add_subparsers(dest="svc_action")

        # install
        svc_subparsers.add_parser("install", help="安装服务")

        # uninstall
        svc_subparsers.add_parser("uninstall", help="卸载服务")

        # enable
        svc_subparsers.add_parser("enable", help="启用开机自启")

        # disable
        svc_subparsers.add_parser("disable", help="禁用开机自启")

        # start
        svc_subparsers.add_parser("start", help="启动服务")

        # stop
        svc_subparsers.add_parser("stop", help="停止服务")

        # restart
        svc_subparsers.add_parser("restart", aliases=["r"], help="重启服务")

        # status
        svc_subparsers.add_parser("status", aliases=["st"], help="查看服务状态")

        # logs
        logs_parser = svc_subparsers.add_parser("logs", aliases=["log"], help="查看服务日志")
        logs_parser.add_argument("-n", "--lines", type=int, default=100, help="显示行数")
        logs_parser.add_argument("-f", "--follow", action="store_true", help="实时跟踪")
        logs_parser.add_argument("--systemd", action="store_true", help="查看 systemd 日志而非 OlivOS 应用日志")

    def _add_adapter_parser(self, subparsers):
        """添加 adapter 命令"""
        parser = subparsers.add_parser(
            "adapter",
            aliases=["a", "adapt"],
            help="适配器管理",
        )
        adapt_subparsers = parser.add_subparsers(dest="adapt_action")

        # list
        adapt_subparsers.add_parser("list", aliases=["ls"], help="列出支持的适配器")

        # enable
        enable_parser = adapt_subparsers.add_parser("enable", help="启用适配器")
        enable_parser.add_argument("name", help="适配器名称")

        # disable
        disable_parser = adapt_subparsers.add_parser("disable", help="禁用适配器")
        disable_parser.add_argument("name", help="适配器名称")

        # config
        cfg_parser = adapt_subparsers.add_parser("config", aliases=["cfg"], help="配置适配器")
        cfg_parser.add_argument("name", help="适配器名称")
        cfg_parser.add_argument("--get", type=str, help="获取配置项")
        cfg_parser.add_argument("--set", type=str, help="设置配置项 (key=value)")

    def _add_account_parser(self, subparsers):
        """添加 account 命令"""
        parser = subparsers.add_parser(
            "account",
            aliases=["acc"],
            help="账号管理",
        )
        acc_subparsers = parser.add_subparsers(dest="acc_action")

        # list
        acc_subparsers.add_parser("list", aliases=["ls"], help="列出所有账号")

        # add
        add_parser = acc_subparsers.add_parser("add", help="添加账号")
        add_parser.add_argument("--adapter", type=str, help="适配器类型 (如: napcat, gocqhttp, telegram, discord)")
        add_parser.add_argument("--id", type=str, help="账号 ID")
        add_parser.add_argument("--token", type=str, help="密码/访问令牌")
        add_parser.add_argument("--host", type=str, help="服务器地址")
        add_parser.add_argument("--port", type=int, help="服务器端口")
        add_parser.add_argument("--access-token", type=str, help="OneBot 访问令牌 (access_token)")
        add_parser.add_argument("--url", type=str, help="服务器 URL (替代 host:port)")
        add_parser.add_argument("--model-type", type=str, help="模型类型 (如: default, public, private)")
        add_parser.add_argument("--debug", action="store_true", help="启用调试模式")
        add_parser.add_argument("--extends", type=str, nargs="+", help="扩展字段 (格式: key=value)")
        add_parser.add_argument("--non-interactive", action="store_true", help="非交互模式")

        # remove
        rm_parser = acc_subparsers.add_parser("remove", aliases=["rm"], help="删除账号")
        rm_parser.add_argument("account_id", help="账号 ID")

        # show
        show_parser = acc_subparsers.add_parser("show", help="显示账号详情")
        show_parser.add_argument("account_id", help="账号 ID")

    def _add_config_parser(self, subparsers):
        """添加 config 命令"""
        parser = subparsers.add_parser(
            "config",
            aliases=["c", "cfg"],
            help="配置管理",
        )
        cfg_subparsers = parser.add_subparsers(dest="cfg_action")

        # show
        cfg_subparsers.add_parser("show", help="显示配置")

        # get
        get_parser = cfg_subparsers.add_parser("get", help="获取配置项")
        get_parser.add_argument("key", help="配置键")

        # set
        set_parser = cfg_subparsers.add_parser("set", help="设置配置项")
        set_parser.add_argument("key", help="配置键")
        set_parser.add_argument("value", help="配置值")

        # unset
        unset_parser = cfg_subparsers.add_parser("unset", help="删除配置项")
        unset_parser.add_argument("key", help="配置键")

        # edit
        cfg_subparsers.add_parser("edit", help="编辑配置文件")

        # reset
        cfg_subparsers.add_parser("reset", help="重置为默认配置")

    def _add_logs_parser(self, subparsers):
        """添加 logs 命令"""
        parser = subparsers.add_parser(
            "logs",
            aliases=["log"],
            help="日志查看",
        )
        parser.add_argument("-n", "--lines", type=int, default=100, help="显示行数")
        parser.add_argument("-f", "--follow", action="store_true", help="实时跟踪")
        parser.add_argument("--pattern", type=str, help="过滤模式")
        parser.add_argument("--cli", action="store_true", help="查看 CLI 工具日志而非 OlivOS 应用日志")

    def _add_status_parser(self, subparsers):
        """添加 status 命令"""
        parser = subparsers.add_parser(
            "status",
            aliases=["st"],
            help="状态监控",
        )
        parser.add_argument("--watch", "-w", action="store_true", help="实时监控")
        parser.add_argument("--health", action="store_true", help="健康检查")

    def _add_run_parser(self, subparsers):
        """添加 run 命令"""
        parser = subparsers.add_parser("run", help="直接运行 OlivOS")
        parser.add_argument("--dev", action="store_true", help="开发模式")
        parser.add_argument("--debug", action="store_true", help="调试模式")

    def _add_update_parser(self, subparsers):
        """添加 update 命令"""
        parser = subparsers.add_parser(
            "update",
            aliases=["up"],
            help="更新 OlivOS-CLI 自身",
        )

    def run(self, args: list[str] = None) -> int:
        """运行 CLI

        Args:
            args: 命令行参数 (默认使用 sys.argv)

        Returns:
            退出码
        """
        # 解析参数
        parsed = self.parser.parse_args(args)

        # 设置日志
        log_level = self.config_manager.config.cli.log_level
        if parsed.verbose:
            log_level = "DEBUG"
        elif parsed.quiet:
            log_level = "ERROR"

        log_file = self.config_manager.config.cli.log_file
        logger.setup(
            log_level=log_level,
            log_file=log_file,
            verbose=parsed.verbose,
            quiet=parsed.quiet,
        )

        # 解析命令别名
        if parsed.command:
            parsed.command = resolve_command_alias(parsed.command)

        # 解析子命令别名
        for attr in dir(parsed):
            if attr.endswith('_action'):
                action = getattr(parsed, attr)
                if action:
                    setattr(parsed, attr, resolve_subcommand_alias(action))

        # 执行命令
        try:
            return self._dispatch_command(parsed)
        except OlivOSCLIError as e:
            logger.error_print(str(e.message))
            return e.exit_code
        except KeyboardInterrupt:
            logger.warning_print("\n操作已取消")
            return 130
        except Exception as e:
            logger.error_print(f"发生错误: {e}")
            return 1

    def _dispatch_command(self, args: argparse.Namespace) -> int:
        """分发命令到对应的处理函数"""
        command = args.command

        if command == "init":
            from .commands.init import cmd_init
            return cmd_init(self.config_manager, args)
        elif command == "git":
            from .commands.git import cmd_git
            return cmd_git(self.config_manager, args)
        elif command == "package":
            from .commands.package import cmd_package
            return cmd_package(self.config_manager, args)
        elif command == "service":
            from .commands.service import cmd_service
            return cmd_service(self.config_manager, args)
        elif command == "adapter":
            from .commands.adapter import cmd_adapter
            return cmd_adapter(self.config_manager, args)
        elif command == "account":
            from .commands.account import cmd_account
            return cmd_account(self.config_manager, args)
        elif command == "config":
            from .commands.config import cmd_config
            return cmd_config(self.config_manager, args)
        elif command == "logs":
            from .commands.logs import cmd_logs
            return cmd_logs(self.config_manager, args)
        elif command == "status":
            from .commands.status import cmd_status
            return cmd_status(self.config_manager, args)
        elif command == "run":
            from .commands.run import cmd_run
            return cmd_run(self.config_manager, args)
        elif command == "update":
            from .commands.update import cmd_update
            return cmd_update(self.config_manager, args)
        else:
            self.parser.print_help()
            return 0


def main(args: list[str] = None) -> int:
    cli = OlivOSCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
