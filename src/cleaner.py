"""阶段 2 · 数据清洗。

按 docs/阶段2-数据清洗与位置映射.md 的清洗规则：年龄计算/筛选、分钟数筛选与
观察名单标记、缺失值处理、去重、数值格式统一。位置映射由 position_mapper 负责。
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from . import position_mapper as pm
from .data_loader import CORE_FIELDS, REQUIRED_FIELDS

# 缺失可安全填 0 的计数型核心字段
_COUNT_FILL_ZERO = [
    "goals", "assists", "shots", "key_passes", "dribbles",
    "passes", "tackles", "interceptions", "yellow_cards", "red_cards",
]


def _ensure_per90(df: pd.DataFrame) -> pd.DataFrame:
    """确保 key_passes_per90 / def_actions_per90 列存在（供 heuristic 使用）。

    从原始计数字段 + minutes 计算每 90 分钟值。
    """
    out = df.copy()
    minutes_raw = out.get("minutes")
    if minutes_raw is None:
        minutes = pd.Series([0] * len(out), index=out.index)
    else:
        minutes = pd.to_numeric(minutes_raw, errors="coerce").fillna(0)
    safe_min = minutes.replace(0, np.nan)

    if "key_passes_per90" not in out.columns:
        kp_raw = out.get("key_passes")
        if kp_raw is None:
            kp = pd.Series([0] * len(out), index=out.index)
        else:
            kp = pd.to_numeric(kp_raw, errors="coerce").fillna(0)
        out["key_passes_per90"] = (kp / safe_min * 90).fillna(0)

    if "def_actions_per90" not in out.columns:
        tkl_raw = out.get("tackles")
        tkl = pd.Series([0] * len(out), index=out.index) if tkl_raw is None else pd.to_numeric(tkl_raw, errors="coerce").fillna(0)
        inc_raw = out.get("interceptions")
        inc = pd.Series([0] * len(out), index=out.index) if inc_raw is None else pd.to_numeric(inc_raw, errors="coerce").fillna(0)
        out["def_actions_per90"] = ((tkl + inc) / safe_min * 90).fillna(0)

    return out


def compute_age_from_dob(dob, ref: date | None = None) -> int | None:
    """由出生日期计算年龄（整岁）。

    Args:
        dob: 出生日期（字符串或可被 pandas 解析的日期）。
        ref: 参考日期，默认今天。

    Returns:
        整岁年龄；无法解析返回 None。
    """
    if dob is None or (isinstance(dob, float) and pd.isna(dob)):
        return None
    ref = ref or date.today()
    ts = pd.to_datetime(dob, errors="coerce")
    if pd.isna(ts):
        return None
    born = ts.date()
    years = ref.year - born.year - ((ref.month, ref.day) < (born.month, born.day))
    return int(years)


def ensure_age(df: pd.DataFrame, ref: date | None = None) -> pd.DataFrame:
    """确保存在 ``age`` 列：缺失时用 ``date_of_birth`` 计算补齐。

    Args:
        df: 输入数据。
        ref: 参考日期。

    Returns:
        含 ``age`` 列的**新** DataFrame。
    """
    out = df.copy()
    if "age" not in out.columns:
        out["age"] = np.nan
    out["age"] = pd.to_numeric(out["age"], errors="coerce")
    if "date_of_birth" in out.columns:
        need = out["age"].isna()
        computed = out.loc[need, "date_of_birth"].apply(
            lambda d: compute_age_from_dob(d, ref)
        )
        out.loc[need, "age"] = pd.to_numeric(computed, errors="coerce")
    out["age"] = pd.to_numeric(out["age"], errors="coerce")
    return out


def filter_age(df: pd.DataFrame, max_age: int = 21) -> pd.DataFrame:
    """只保留 ``age <= max_age`` 的球员（年龄缺失的剔除）。"""
    out = df.copy()
    return out[out["age"].notna() & (out["age"] <= max_age)].reset_index(drop=True)


def mark_eligibility(df: pd.DataFrame, min_minutes: int = 600) -> pd.DataFrame:
    """新增 ``is_official`` 列：分钟数 ≥ 阈值为正式评分，否则进观察名单。

    分钟数缺失视为 0（不达标）。
    """
    out = df.copy()
    minutes = pd.to_numeric(out.get("minutes"), errors="coerce").fillna(0)
    out["minutes"] = minutes
    out["is_official"] = minutes >= min_minutes
    return out


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """缺失值处理：必须字段缺失的行剔除；计数型核心字段缺失填 0。

    百分比/增强字段保持原样（NaN），由阶段 3 计算数据完整度。
    """
    out = df.copy()
    # 必须字段缺失的行剔除（这些列必须存在且非空）
    present_required = [c for c in REQUIRED_FIELDS if c in out.columns]
    if present_required:
        out = out.dropna(subset=present_required).reset_index(drop=True)
    # 计数型核心字段缺失填 0
    for col in _COUNT_FILL_ZERO:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """去重：有 ``player_id`` 优先按其去重，否则按 ``player_name+team+league``。"""
    out = df.copy()
    if "player_id" in out.columns and out["player_id"].notna().any():
        return out.drop_duplicates(subset=["player_id"], keep="first").reset_index(drop=True)
    keys = [c for c in ("player_name", "team", "league") if c in out.columns]
    if keys:
        return out.drop_duplicates(subset=keys, keep="first").reset_index(drop=True)
    return out.drop_duplicates(keep="first").reset_index(drop=True)


def compute_data_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """新增 ``data_completeness`` 列：核心字段实际有值的比例（0-1）。

    仅统计数据中实际存在的核心字段列。
    """
    out = df.copy()
    core_cols = [c for c in CORE_FIELDS if c in out.columns]
    if not core_cols:
        out["data_completeness"] = 0.0
        return out
    filled = out[core_cols].notna().sum(axis=1)
    out["data_completeness"] = filled / len(core_cols)
    return out


def clean(
    df: pd.DataFrame,
    pos_map: dict[str, str],
    max_age: int = 21,
    min_minutes: int = 600,
    scoring_positions: set[str] | None = None,
    ref: date | None = None,
) -> pd.DataFrame:
    """执行阶段 2 完整清洗流程，返回可评分数据集。

    步骤：位置映射 → 年龄补齐/筛选 → 分钟数标记 → 缺失处理 → 去重 →
    数据完整度 → 过滤到评分位置。

    Args:
        df: 阶段 1 的原始 DataFrame（已列名归一化）。
        pos_map: position_mapping.yaml。
        max_age: 最大年龄阈值。
        min_minutes: 正式评分最低分钟数。
        scoring_positions: 参与评分的标准分组集合，默认 {Winger,AM,CM,DM}。
        ref: 年龄计算参考日期。

    Returns:
        清洗并过滤后的**新** DataFrame（含 standard_position / is_official /
        data_completeness 等列）。
    """
    scoring_positions = scoring_positions or set(pm.STANDARD_GROUPS)

    out = _ensure_per90(df)
    out = pm.add_standard_position(out, pos_map)
    out = ensure_age(out, ref)
    out = filter_age(out, max_age)
    out = mark_eligibility(out, min_minutes)
    out = handle_missing(out)
    out = dedupe(out)
    out = compute_data_completeness(out)
    # 只保留能归入评分分组的球员
    out = out[out["standard_position"].isin(scoring_positions)].reset_index(drop=True)
    return out
