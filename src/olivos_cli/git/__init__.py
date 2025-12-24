# -*- coding: utf-8 -*-
"""
Git 操作模块
"""

from pathlib import Path
from typing import Optional

from rich.console import Console

from ..core.exceptions import GitError
from ..core.logger import get_logger
from ..utils import check_command, run_command, run_command_stream

logger = get_logger()


class GitOperator:
    """Git 操作器"""

    def __init__(self, console: Optional[Console] = None, verbose: bool = False):
        self.console = console or logger.console
        self.verbose = verbose

    def check_git(self) -> bool:
        """检查 git 是否可用"""
        return check_command("git")

    def ensure_git(self) -> None:
        """确保 git 可用"""
        if not self.check_git():
            raise GitError("git 未安装，请先安装 git")

    def clone(
        self,
        repo_url: str,
        target_dir: Path,
        branch: str = "main",
        depth: int = 1,
        mirror_url: Optional[str] = None,
        use_mirror: bool = False,
        force: bool = False,
    ) -> bool:
        """克隆仓库

        Args:
            repo_url: 仓库地址
            target_dir: 目标目录
            branch: 分支名称
            depth: 克隆深度 (0 = 完整克隆)
            mirror_url: 镜像地址
            use_mirror: 是否使用镜像
            force: 是否强制覆盖

        Returns:
            是否成功
        """
        self.ensure_git()

        # 确定实际使用的 URL
        url = mirror_url if use_mirror and mirror_url else repo_url

        # 检查目标目录
        if target_dir.exists():
            if not force:
                logger.warning_print(f"目标目录已存在: {target_dir}")
                return False
            import shutil

            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                raise GitError(f"无法删除现有目录: {e}") from e

        # 构建命令
        cmd = ["git", "clone", "-b", branch]
        if depth > 0:
            cmd.extend(["--depth", str(depth)])
        cmd.extend([str(url), str(target_dir)])

        # 执行克隆
        logger.step(f"正在克隆 {url} 到 {target_dir}")

        if self.verbose:
            # 使用流式输出
            returncode = run_command_stream(
                cmd,
                line_callback=lambda line: logger.verbose(line),
                error_callback=lambda line: logger.verbose(line),
            )
            if returncode != 0:
                raise GitError(f"克隆失败，返回码: {returncode}")
        else:
            result = run_command(cmd, check=False)
            if result.returncode != 0:
                raise GitError(f"克隆失败: {result.stderr}")

        logger.success(f"克隆成功: {target_dir}")
        return True

    def pull(
        self,
        repo_dir: Path,
        branch: Optional[str] = None,
    ) -> bool:
        """拉取更新

        Args:
            repo_dir: 仓库目录
            branch: 分支名称 (可选)

        Returns:
            是否成功
        """
        self.ensure_git()

        if not repo_dir.exists():
            raise GitError(f"仓库目录不存在: {repo_dir}")

        logger.step("正在获取远程更新...")

        if self.verbose:
            returncode = run_command_stream(
                ["git", "fetch"],
                cwd=str(repo_dir),
                line_callback=lambda line: logger.verbose(line),
                error_callback=lambda line: logger.verbose(line),
            )
            if returncode != 0:
                raise GitError(f"fetch 失败，返回码: {returncode}")
        else:
            result = run_command(["git", "fetch"], cwd=str(repo_dir), check=False)
            if result.returncode != 0:
                raise GitError(f"fetch 失败: {result.stderr}")

        cmd = ["git", "pull"]
        if branch:
            cmd.extend(["origin", branch])

        if self.verbose:
            returncode = run_command_stream(
                cmd,
                cwd=str(repo_dir),
                line_callback=lambda line: logger.verbose(line),
                error_callback=lambda line: logger.verbose(line),
            )
            if returncode != 0:
                raise GitError(f"pull 失败，返回码: {returncode}")
        else:
            result = run_command(cmd, cwd=str(repo_dir), check=False)
            if result.returncode != 0:
                raise GitError(f"pull 失败: {result.stderr}")

        logger.success(f"更新成功: {repo_dir}")
        return True

    def checkout(
        self,
        repo_dir: Path,
        ref: str,
    ) -> bool:
        """切换分支或检出到指定提交

        Args:
            repo_dir: 仓库目录
            ref: 分支名或 commit hash

        Returns:
            是否成功
        """
        self.ensure_git()

        if not repo_dir.exists():
            raise GitError(f"仓库目录不存在: {repo_dir}")

        cmd = ["git", "checkout", ref]

        if self.verbose:
            returncode = run_command_stream(
                cmd,
                cwd=str(repo_dir),
                line_callback=lambda line: logger.verbose(line),
                error_callback=lambda line: logger.verbose(line),
            )
            if returncode != 0:
                raise GitError(f"checkout 失败，返回码: {returncode}")
        else:
            result = run_command(cmd, cwd=str(repo_dir), check=False)
            if result.returncode != 0:
                raise GitError(f"checkout 失败: {result.stderr}")

        logger.success(f"已切换到: {ref}")
        return True

    def get_current_branch(self, repo_dir: Path) -> str:
        """获取当前分支名"""
        self.ensure_git()

        cmd = ["git", "branch", "--show-current"]
        result = run_command(cmd, cwd=str(repo_dir), capture=True)

        if result.returncode != 0:
            raise GitError(f"获取分支失败: {result.stderr}")

        return result.stdout.strip()

    def get_current_commit(self, repo_dir: Path) -> str:
        """获取当前 commit hash"""
        self.ensure_git()

        cmd = ["git", "rev-parse", "HEAD"]
        result = run_command(cmd, cwd=str(repo_dir), capture=True)

        if result.returncode != 0:
            raise GitError(f"获取 commit 失败: {result.stderr}")

        return result.stdout.strip()

    def get_repo_status(self, repo_dir: Path) -> dict:
        """获取仓库状态"""
        self.ensure_git()

        if not repo_dir.exists():
            return {"exists": False}

        try:
            branch = self.get_current_branch(repo_dir)
            commit = self.get_current_commit(repo_dir)

            # 检查是否有未提交的更改
            cmd = ["git", "status", "--porcelain"]
            result = run_command(cmd, cwd=str(repo_dir), capture=True)
            dirty = result.returncode == 0 and bool(result.stdout.strip())

            # 检查是否有未推送的提交
            cmd = ["git", "log", f"origin/{branch}..HEAD", "--oneline"]
            result = run_command(cmd, cwd=str(repo_dir), capture=True)
            ahead = result.returncode == 0 and len(result.stdout.strip().split("\n")) > 0

            return {
                "exists": True,
                "branch": branch,
                "commit": commit,
                "dirty": dirty,
                "ahead": ahead,
            }
        except GitError:
            return {"exists": True, "error": True}


__all__ = [
    "GitOperator",
]
