"""配置加载工具（阶段 0-9 共用）。

负责读取 config/ 下的 YAML 配置文件，并提供常用的路径解析。
参见 docs/00-总览与架构.md 第 8 节。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# 项目根目录（src 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml(path: str | Path) -> Any:
    """读取一个 YAML 文件并返回解析后的对象。

    Args:
        path: YAML 文件路径（绝对或相对项目根目录）。

    Returns:
        解析后的 Python 对象（通常是 dict）。

    Raises:
        FileNotFoundError: 文件不存在。
    """
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    if not p.exists():
        raise FileNotFoundError(f"配置文件不存在: {p}")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(name: str = "config.yaml") -> dict:
    """读取 config/ 目录下的配置文件，返回字典。

    Args:
        name: 配置文件名（默认 config.yaml）。

    Returns:
        配置字典；空文件返回空字典。
    """
    data = load_yaml(CONFIG_DIR / name)
    return data or {}
