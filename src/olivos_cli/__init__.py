# -*- coding: utf-8 -*-
from importlib.metadata import version

try:
    __version__ = version("olivos_cli")
except Exception:
    __version__ = "builtin"

from .cli.main import main

__all__ = ["__version__", "main"]
