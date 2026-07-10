"""阶段 5 · Opta 联赛强度修正。

读取 Opta Power Rankings 配置，把联赛映射为 0-100 的强度分。
参见 docs/阶段5-Opta联赛强度修正.md。
"""
from __future__ import annotations

import pandas as pd

# 默认值：未收录联赛的强度分（中性值 50，表示无偏袒）
_DEFAULT_SCORE = 50.0


def load_league_strength(strength_cfg: dict) -> dict[str, float]:
    """从 league_strength_opta.yaml 中提取 league→score 映射。

    Args:
        strength_cfg: YAML 配置解析结果。

    Returns:
        ``{联赛归一化名: 0-100 强度分}`` 字典。
    """
    leagues = strength_cfg.get("leagues", {})
    return {str(k): float(v) for k, v in leagues.items()}


def apply_league_strength(
    df: pd.DataFrame,
    strength_map: dict[str, float],
    league_col: str = "league",
) -> pd.Series:
    """根据联赛列查表返回每个球员的联赛强度分。

    未收录的联赛返回默认值 50（中性）。

    Args:
        df: 含 league 列的 DataFrame。
        strength_map: league→score 映射。
        league_col: 联赛列名。

    Returns:
        每个球员的 0-100 联赛强度分 Series。
    """
    return df[league_col].map(strength_map).fillna(_DEFAULT_SCORE)
