"""阶段 3 · 特征计算。

把累计计数字段换算为 per90 效率指标，消除出场时间差异。
参见 docs/阶段3-特征计算.md。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# 需计算 per90 的核心字段
_PER90_COUNT_FIELDS = [
    "goals", "assists", "shots", "key_passes", "dribbles",
    "passes", "tackles", "interceptions", "yellow_cards", "red_cards",
]

# 增强字段（有则计算 per90）
_PER90_ENHANCE_FIELDS = [
    "xg", "xa", "progressive_carries", "shot_creating_actions",
]


def _safe_numeric(series: pd.Series) -> pd.Series:
    """安全转数值：先处理欧洲小数格式（逗号→点），再 pd.to_numeric。"""
    s = series.astype(str).str.replace(",", ".").str.strip()
    return pd.to_numeric(s, errors="coerce").fillna(0)


def _safe_per90(values: pd.Series, minutes: pd.Series) -> pd.Series:
    """安全计算 per90：minutes 为 0 或 NaN 时返回 0。"""
    safe = minutes.replace(0, np.nan)
    return (values / safe * 90).fillna(0)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """从清洗后数据计算全部 per90 特征。

    对核心计数字段和增强字段生成 ``*_per90`` 列，
    同时确保已有 per90 列（如 key_passes_per90）不被覆盖。

    Args:
        df: 阶段 2 输出的清洗后 DataFrame（含 minutes、各计数字段）。

    Returns:
        新增 per90 列的**新** DataFrame。
    """
    out = df.copy()

    # 修复欧洲小数格式（逗号→点）：FBref 数据集部分列用逗号做小数点
    _fix_cols = ["xg", "xa", "Expected_npxG", "Expected_npxG+xAG",
                 "Expected_xA", "xAG_"]
    for c in _fix_cols:
        if c in out.columns:
            out[c] = _safe_numeric(out[c])

    minutes = pd.to_numeric(out["minutes"], errors="coerce").fillna(0)

    # 核心字段 per90
    for col in _PER90_COUNT_FIELDS:
        target = f"{col}_per90"
        if target not in out.columns and col in out.columns:
            raw = _safe_numeric(out[col])
            out[target] = _safe_per90(raw, minutes)

    # 增强字段 per90
    for col in _PER90_ENHANCE_FIELDS:
        target = f"{col}_per90"
        if target not in out.columns and col in out.columns:
            raw = _safe_numeric(out[col])
            out[target] = _safe_per90(raw, minutes)

    # 确保 key_passes_per90 / def_actions_per90 存在（由阶段 2 生成或被上面计算）
    if "key_passes_per90" not in out.columns and "key_passes" in out.columns:
        out["key_passes_per90"] = _safe_per90(
            pd.to_numeric(out["key_passes"], errors="coerce").fillna(0), minutes
        )
    if "def_actions_per90" not in out.columns:
        tkl_raw = out.get("tackles")
        tkl = pd.Series([0] * len(out), index=out.index) if tkl_raw is None else pd.to_numeric(tkl_raw, errors="coerce").fillna(0)
        inc_raw = out.get("interceptions")
        inc = pd.Series([0] * len(out), index=out.index) if inc_raw is None else pd.to_numeric(inc_raw, errors="coerce").fillna(0)
        out["def_actions_per90"] = _safe_per90(tkl + inc, minutes)

    return out
