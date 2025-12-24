# -*- coding: utf-8 -*-
"""
git 命令实现
"""

from ...core import ConfigManager, get_logger
from ...core.exceptions import GitError
from ...git import GitOperator

logger = get_logger()


def cmd_git(config_manager: ConfigManager, args) -> int:
    """Git 仓库管理"""
    action = args.git_action

    if not action:
        # 显示帮助信息
        logger.info_print("用法: olivos-cli git [ACTION] [OPTIONS]")
        logger.info_print("")
        logger.info_print("动作:")
        logger.info_print("  clone         克隆仓库")
        logger.info_print("  pull (up)     拉取更新")
        logger.info_print("  checkout (co) 切换分支/提交")
        logger.info_print("  status (st)   查看状态")
        logger.info_print("")
        logger.info_print("使用 'olivos-cli git [ACTION] --help' 查看具体动作的帮助")
        return 0

    config = config_manager.config
    install_path = config.git.expanded_install_path

    git = GitOperator()

    if action == "clone":
        return _cmd_git_clone(git, config, args)
    elif action == "pull":
        return _cmd_git_pull(git, install_path, args)
    elif action == "checkout":
        return _cmd_git_checkout(git, install_path, args)
    elif action == "status":
        return _cmd_git_status(git, install_path)

    return 0


def _cmd_git_clone(git: GitOperator, config, args) -> int:
    """克隆仓库"""
    branch = args.branch or config.git.branch
    use_mirror = args.mirror or config.git.use_mirror

    logger.step(f"克隆 OlivOS 仓库 (分支: {branch})")

    try:
        git.clone(
            repo_url=config.git.repo_url,
            target_dir=config.git.expanded_install_path,
            branch=branch,
            mirror_url=config.git.mirror_url,
            use_mirror=use_mirror,
            force=args.force,
        )
        return 0
    except GitError as e:
        logger.error_print(str(e))
        return 1


def _cmd_git_pull(git: GitOperator, install_path, args) -> int:
    """拉取更新"""
    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        logger.info_print("请先运行: olivos-cli init")
        return 1

    logger.step("拉取更新...")

    try:
        git.pull(install_path, branch=args.branch)
        return 0
    except GitError as e:
        logger.error_print(str(e))
        return 1


def _cmd_git_checkout(git: GitOperator, install_path, args) -> int:
    """切换分支/提交"""
    if not install_path.exists():
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        return 1

    logger.step(f"切换到: {args.ref}")

    try:
        git.checkout(install_path, args.ref)
        return 0
    except GitError as e:
        logger.error_print(str(e))
        return 1


def _cmd_git_status(git: GitOperator, install_path) -> int:
    """查看状态"""
    status = git.get_repo_status(install_path)

    if not status.get("exists"):
        logger.error_print(f"OlivOS 目录不存在: {install_path}")
        return 1

    from rich.console import Console
    from rich.table import Table

    console = logger.console

    table = Table(title="Git 仓库状态")
    table.add_column("项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("分支", status.get("branch", "-"))
    table.add_row("提交", status.get("commit", "-")[:8])
    table.add_row("有未提交更改", "[red]是[/red]" if status.get("dirty") else "[green]否[/green]")
    table.add_row("有未推送提交", "[red]是[/red]" if status.get("ahead") else "[green]否[/green]")

    console.print(table)
    return 0
