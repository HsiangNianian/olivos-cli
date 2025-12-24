# -*- coding: utf-8 -*-
"""
交互式输入工具
"""

from typing import Any, Optional

from rich.prompt import Confirm, Prompt


def ask(
    question: str,
    default: Optional[str] = None,
    password: bool = False,
    choices: Optional[list[str]] = None,
) -> str:
    """询问用户输入

    Args:
        question: 问题文本
        default: 默认值
        password: 是否为密码
        choices: 可选值列表

    Returns:
        用户输入的值
    """
    from rich.console import Console

    console = Console()
    result = Prompt.ask(
        question,
        default=default,
        password=password,
        choices=choices,
        console=console,
    )
    return result if result is not None else (default or "")


def confirm(question: str, default: bool = False) -> bool:
    """确认操作

    Args:
        question: 问题文本
        default: 默认值

    Returns:
        用户选择
    """
    return Confirm.ask(question, default=default)


def select(question: str, choices: list[str], default: Optional[int] = None) -> str:
    """从列表中选择一个

    Args:
        question: 问题文本
        choices: 选项列表
        default: 默认选项索引

    Returns:
        选择的值
    """
    from rich.console import Console

    console = Console()
    console.print(f"\n[bold cyan]{question}[/bold cyan]")

    for i, choice in enumerate(choices):
        marker = "[bold cyan]>[/bold cyan]" if i == default else " "
        console.print(f"  {marker} [{i}] {choice}")

    while True:
        try:
            answer = Prompt.ask(
                "请选择",
                default=str(default) if default is not None else None,
                console=console,
            )
            # 处理空输入
            if not answer or answer.strip() == "":
                if default is not None:
                    answer = str(default)
                else:
                    console.print("[red]无效的输入，请输入数字[/red]")
                    continue
            # 处理数字输入
            if answer.strip().isdigit():
                index = int(answer.strip())
                if 0 <= index < len(choices):
                    return choices[index]
                console.print("[red]无效的选择，请重试[/red]")
            # 处理 "?" 显示帮助信息
            elif answer.strip() == "?":
                console.print("[dim]提示: 输入数字来选择对应的选项[/dim]")
                console.print("[dim]例如，输入 0 选择第一个选项，输入 1 选择第二个选项[/dim]")
            else:
                console.print("[red]无效的输入，请输入数字或 ? 查看帮助[/red]")
        except KeyboardInterrupt:
            console.print("[yellow]操作已取消[/yellow]")
            raise


def select_multiple(
    question: str,
    choices: list[str],
    min_select: int = 1,
    max_select: Optional[int] = None,
) -> list[str]:
    """从列表中选择多个

    Args:
        question: 问题文本
        choices: 选项列表
        min_select: 最少选择数量
        max_select: 最多选择数量（None 表示不限制）

    Returns:
        选择的值列表
    """
    from rich.console import Console

    console = Console()
    console.print(f"\n[bold cyan]{question}[/bold cyan]")
    console.print("[dim]提示: 输入数字用空格分隔，如: 0 1 3[/dim]")

    for i, choice in enumerate(choices):
        console.print(f"    [{i}] {choice}")

    while True:
        try:
            answer = Prompt.ask(
                f"请选择 (最少 {min_select} 项" +
                (f", 最多 {max_select} 项" if max_select else "") +
                ")",
                console=console,
            )

            # 处理 "?" 显示帮助信息
            if answer.strip() == "?":
                console.print("[dim]提示: 输入数字用空格分隔来选择多个选项[/dim]")
                console.print("[dim]例如，输入 0 1 3 选择第1、第2和第4个选项[/dim]")
                continue

            # 解析输入
            indices = []
            for part in answer.strip().split():
                if not part.isdigit():
                    console.print("[red]无效的输入，请输入用空格分隔的数字[/red]")
                    break
                indices.append(int(part))

            # 检查范围
            if any(i < 0 or i >= len(choices) for i in indices):
                console.print(f"[red]选择超出范围 (0-{len(choices)-1})，请重试[/red]")
                continue

            # 检查重复
            unique_indices = list(dict.fromkeys(indices))  # 保持顺序去重
            if len(unique_indices) < len(indices):
                console.print("[yellow]已去除重复的选择[/yellow]")
                indices = unique_indices

            # 检查数量
            if len(indices) < min_select:
                console.print(f"[red]至少需要选择 {min_select} 项[/red]")
                continue
            if max_select and len(indices) > max_select:
                console.print(f"[red]最多只能选择 {max_select} 项[/red]")
                continue

            return [choices[i] for i in indices]

        except KeyboardInterrupt:
            console.print("[yellow]操作已取消[/yellow]")
            raise


__all__ = ["ask", "confirm", "select", "select_multiple"]
