# -*- coding: utf-8 -*-
"""
init 命令实现
"""

import os
import platform
import sys
from collections import deque
from pathlib import Path

from ...core import CONFIG_DIR, ConfigManager, get_logger
from ...core.exceptions import GitError, PackageError
from ...git import GitOperator
from ...package import get_package_manager
from ...utils import get_requirements_file, run_command_stream

logger = get_logger()

# 虚拟环境目录名
VENV_DIR = ".venv"


def _create_venv(install_path: Path, python_path: str, verbose: bool = False, system_site_packages: bool = False) -> Path:
    """创建虚拟环境

    Args:
        install_path: OlivOS 安装路径
        python_path: Python 可执行文件路径
        verbose: 是否显示详细输出
        system_site_packages: 是否允许访问系统站点包

    Returns:
        虚拟环境路径
    """
    venv_path = install_path / VENV_DIR

    if venv_path.exists():
        logger.info_print(f"虚拟环境已存在: {venv_path}")
        return venv_path

    logger.step(f"创建虚拟环境: {venv_path}")
    if system_site_packages:
        logger.info_print("启用 system-site-packages（可访问系统已安装的包）")

    # 使用标准库 venv 创建虚拟环境
    import subprocess

    cmd = [python_path, "-m", "venv", str(venv_path)]
    if system_site_packages:
        cmd.append("--system-site-packages")

    if verbose:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in process.stdout:
            logger.verbose(line.strip())
        returncode = process.wait()
        if returncode != 0:
            raise PackageError(f"虚拟环境创建失败，返回码: {returncode}")
    else:
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise PackageError(f"虚拟环境创建失败: {result.stderr.decode()}")

    logger.success(f"虚拟环境创建成功: {venv_path}")
    return venv_path


def _get_venv_python(install_path: Path) -> Path:
    """获取虚拟环境中的 Python 路径"""
    venv_path = install_path / VENV_DIR

    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def cmd_init(config_manager: ConfigManager, args) -> int:
    """初始化并安装 OlivOS"""
    # 确保配置目录存在
    config_manager.ensure_dirs()

    # 如果配置不存在，创建默认配置
    if not config_manager.config_path.exists():
        config_manager.init_default_config()
    else:
        config_manager.load()

    # 保存选择的包管理器
    if hasattr(args, 'package_manager') and args.package_manager:
        config_manager.config.package.manager = args.package_manager
        config_manager.save()
        logger.info_print(f"包管理器设置为: {args.package_manager}")

    # 获取安装路径（确保是绝对路径）
    install_path = Path(args.path).resolve() if args.path else config_manager.config.git.expanded_install_path.resolve()
    branch = args.branch or config_manager.config.git.branch
    use_mirror = args.mirror or config_manager.config.git.use_mirror
    verbose = getattr(args, 'verbose', False) or config_manager.config.cli.verbose

    logger.step(f"初始化 OlivOS 到: {install_path}")
    logger.step(f"分支: {branch}")
    logger.step(f"Python 版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    logger.step(f"包管理器: {config_manager.config.package.manager}")
    if use_mirror:
        logger.info_print("使用镜像源")

    # Clone 仓库
    git = GitOperator(verbose=verbose)
    try:
        git.clone(
            repo_url=config_manager.config.git.repo_url,
            target_dir=install_path,
            branch=branch,
            mirror_url=config_manager.config.git.mirror_url,
            use_mirror=use_mirror,
            force=True,
        )
    except GitError as e:
        logger.error_print(str(e))
        return 1

    # 保存绝对路径到配置
    config_manager.config.git.install_path = str(install_path)
    config_manager.save()

    # 创建虚拟环境
    if args.no_deps:
        logger.info_print("跳过虚拟环境创建和依赖安装")
        venv_path = None
    else:
        try:
            venv_path = _create_venv(
                install_path,
                python_path=sys.executable,
                verbose=verbose,
            )
        except PackageError as e:
            logger.error_print(str(e))
            logger.info_print("提示: 可以跳过依赖安装: olivos-cli init --no-deps")
            return 1

    # 安装依赖
    if args.no_deps:
        logger.info_print("跳过依赖安装")
    else:
        logger.step("安装依赖...")

        # 优先使用指定的依赖文件
        if hasattr(args, 'requirements') and args.requirements:
            requirements_file = install_path / args.requirements
        else:
            requirements_file = get_requirements_file(install_path)

        logger.verbose(f"选择的依赖文件: {requirements_file.name}")

        # 检查兼容性并显示警告
        from ...utils import check_requirements_compatibility
        warnings = check_requirements_compatibility(requirements_file)
        for warning in warnings:
            logger.warning_print(warning)

        if requirements_file.exists():
            try:
                pkg_mgr = get_package_manager(
                    name=config_manager.config.package.manager,
                    auto_install=config_manager.config.package.auto_install,
                    index_url=config_manager.config.package.uv.index_url,
                    verbose=True,  #! 强制启用 verbose 以显示实时日志
                )
                # 在虚拟环境中安装依赖
                pkg_mgr.install_venv(install_path, venv_path, requirements_file)
            except PackageError as e:
                error_msg = str(e)
                # 检查是否是 Pillow 编译失败, 目前Pillow只在10.0.0支持了Python3.12, 所以理论上OlivOS不支持Python3.12
                if "pillow" in error_msg.lower() or "Pillow" in error_msg:
                    logger.warning_print("Pillow 安装失败，尝试使用系统 Pillow...")
                    if _try_install_with_system_pillow(install_path, venv_path, requirements_file, verbose=True):
                        logger.success("依赖安装成功（使用系统 Pillow）")
                    else:
                        logger.error_print("依赖安装失败")
                        logger.info_print("")
                        logger.info_print("请尝试以下方案之一:")
                        logger.info_print("  1. 安装系统 Pillow: python-pillow")
                        logger.info_print("  2. 跳过依赖安装: olivos-cli init --no-deps")
                        return 1
                else:
                    logger.error_print(str(e))
                    logger.info_print("")
                    logger.info_print("提示: 可以跳过依赖安装: olivos-cli init --no-deps")
                    return 1
        else:
            logger.warning_print(f"未找到依赖文件: {requirements_file.name}")

    # 创建配置目录
    (install_path / "conf").mkdir(parents=True, exist_ok=True)
    (install_path / "plugin").mkdir(parents=True, exist_ok=True)
    (install_path / "data").mkdir(parents=True, exist_ok=True)

    logger.success("OlivOS 初始化完成!")
    logger.info_print(f"安装路径: {install_path}")
    logger.info_print(f"虚拟环境: {install_path / VENV_DIR}")
    logger.info_print(f"配置文件: {install_path / 'conf'}")

    if not args.no_deps:
        logger.info_print("")
        logger.info_print("下一步:")
        logger.info_print("  1. 配置账号: olivos-cli account add")
        logger.info_print("  2. 安装服务: olivos-cli service install")
        logger.info_print("  3. 启动服务: olivos-cli service start")
        logger.info_print("")
        logger.info_print("手动运行 OlivOS:")
        logger.info_print(f"  cd {install_path}")
        logger.info_print(f"  {VENV_DIR}/bin/python main.py")

    return 0


def _try_install_with_system_pillow(install_path: Path, venv_path: Path, requirements_file: Path, verbose: bool) -> bool:
    """使用系统 Pillow，跳过 Pillow 的安装

    Args:
        install_path: OlivOS 安装路径
        venv_path: 虚拟环境路径
        requirements_file: 依赖文件
        verbose: 是否显示详细输出

    Returns:
        是否成功
    """
    import subprocess
    import sys
    import shutil

    # 检查系统是否有 Pillow (通过 pacman/dpkg/等)
    system_pillow = False
    if shutil.which("pacman"):
        try:
            subprocess.run(
                ["pacman", "-Qi", "python-pillow"],
                capture_output=True,
                check=True,
            )
            system_pillow = True
            logger.info_print("检测到系统 Pillow (pacman)")
        except subprocess.CalledProcessError:
            pass
    elif shutil.which("dpkg"):
        try:
            subprocess.run(
                ["dpkg", "-s", "python3-pil"],
                capture_output=True,
                check=True,
            )
            system_pillow = True
            logger.info_print("检测到系统 Pillow (apt)")
        except subprocess.CalledProcessError:
            pass
    elif shutil.which("rpm"):
        try:
            subprocess.run(
                ["rpm", "-q", "python3-pillow"],
                capture_output=True,
                check=True,
            )
            system_pillow = True
            logger.info_print("检测到系统 Pillow (rpm)")
        except subprocess.CalledProcessError:
            pass

    if not system_pillow:
        logger.warning_print("未检测到系统 Pillow")
        logger.info_print("请安装系统 Pillow: sudo pacman -S python-pillow")
        return False

    # 删除旧的 venv，重新创建带 system-site-packages 的
    logger.info_print("重新创建虚拟环境（启用 system-site-packages）...")
    try:
        shutil.rmtree(venv_path)
    except Exception as e:
        logger.warning_print(f"删除旧虚拟环境失败: {e}")
        return False

    try:
        _create_venv(install_path, sys.executable, verbose, system_site_packages=True)
    except Exception as e:
        logger.error_print(f"创建虚拟环境失败: {e}")
        return False

    # 创建过滤后的 requirements 文件（移除 Pillow）
    filtered_requirements = install_path / "requirements_no_pillow.txt"
    with open(requirements_file, "r") as f:
        lines = f.readlines()

    filtered_lines = []
    pillow_skipped = False
    for line in lines:
        line_stripped = line.strip()
        line_lower = line.lower()
        # 跳过 Pillow 相关的行
        if "pillow" in line_lower:
            pillow_skipped = True
            logger.verbose(f"跳过: {line_stripped}")
            continue
        # 跳过空行和注释
        if line_stripped and not line_stripped.startswith("#"):
            filtered_lines.append(line)

    if pillow_skipped:
        logger.info_print("已跳过 Pillow（将使用系统版本）")

    if not filtered_lines:
        logger.warning_print("过滤后没有其他依赖需要安装")
        return True

    with open(filtered_requirements, "w") as f:
        f.writelines(filtered_lines)

    logger.verbose(f"创建过滤后的依赖文件: {filtered_requirements.name}")

    # 使用虚拟环境的 pip 安装其他依赖
    if sys.platform == "win32":
        python_bin = venv_path / "Scripts" / "python.exe"
    else:
        python_bin = venv_path / "bin" / "python"

    cmd = [str(python_bin), "-m", "pip", "install", "-r", str(filtered_requirements)]
    if verbose:
        # 使用限制输出模式（只显示最后几行）
        returncode = _run_command_limited(cmd, str(install_path))
        if returncode != 0:
            logger.error_print(f"依赖安装失败，返回码: {returncode}")
            filtered_requirements.unlink(missing_ok=True)
            return False
    else:
        result = subprocess.run(cmd, cwd=str(install_path), capture_output=True)
        if result.returncode != 0:
            logger.error_print(f"依赖安装失败: {result.stderr.decode()}")
            filtered_requirements.unlink(missing_ok=True)
            return False

    # 清理临时文件
    filtered_requirements.unlink(missing_ok=True)

    return True


def _run_command_limited(cmd, cwd: str, max_lines: int = 4) -> int:
    """运行命令，实时滚动显示最后几行输出

    Args:
        cmd: 命令列表
        cwd: 工作目录
        max_lines: 最多显示的行数

    Returns:
        返回码
    """
    import subprocess
    import sys
    from collections import deque

    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # 使用 deque 保存最后几行
    output_buffer = deque(maxlen=max_lines)

    for line in process.stdout:
        line = line.strip()
        if line:
            output_buffer.append(line)
            # 清除并重新打印
            sys.stdout.write("\r\033[K")  # 清除当前行
            if len(output_buffer) > 0:
                sys.stdout.write(f"\033[{len(output_buffer)}F")
            for buffered_line in output_buffer:
                sys.stdout.write("\r\033[K")
                sys.stdout.write(f"  {buffered_line}\n")
            sys.stdout.flush()

    returncode = process.wait()
    print()  # 换行

    return returncode
