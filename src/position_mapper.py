"""阶段 2 · 位置映射（方案 B）。

按优先级把球员映射到标准位置分组 Winger / AM / CM / DM：
1. Transfermarkt 主位置（阶段 0 补齐，命名近 1:1）→ position_mapping.yaml
2. FBref 粗位置 + 启发式（匹配不上时兜底）

参见 docs/阶段2-数据清洗与位置映射.md。
"""
from __future__ import annotations

import pandas as pd

# 标准分组
WINGER, AM, CM, DM = "Winger", "AM", "CM", "DM"
STANDARD_GROUPS = {WINGER, AM, CM, DM}

# 位置来源标记
SRC_TM = "transfermarkt"
SRC_HEURISTIC = "heuristic"
SRC_NONE = "none"


def map_transfermarkt_position(
    tm_position, pos_map: dict[str, str]
) -> str | None:
    """把 Transfermarkt 主位置字符串映射为标准分组。

    大小写不敏感；未收录或空值返回 None。

    Args:
        tm_position: TM 主位置（如 ``"Right Winger"``）。
        pos_map: position_mapping.yaml 解析结果。

    Returns:
        标准分组（Winger/AM/CM/DM）或 None。
    """
    if tm_position is None or (isinstance(tm_position, float) and pd.isna(tm_position)):
        return None
    key = str(tm_position).strip().lower()
    lowered = {k.lower(): v for k, v in pos_map.items()}
    return lowered.get(key)


def heuristic_position(
    fbref_pos, key_passes_per90=None, def_actions_per90=None
) -> str | None:
    """FBref 粗位置 + 指标比值的启发式分组（第 0 层兜底）。

    规则：
    - 含 FW 的 → Winger（MVP 近似：进攻边路球员）。
    - 纯 MF → 用创造力(key_passes)与防守参与(tackles+interceptions)比值：
      创造力明显更强 → AM；防守参与明显更强 → DM；否则 CM。
    - DF/GK 或无法判断 → None（不进入评分）。

    Args:
        fbref_pos: FBref 粗位置字符串（如 ``"FW"``、``"MF,FW"``、``"DF"``）。
        key_passes_per90: 每 90 分钟关键传球（可空）。
        def_actions_per90: 每 90 分钟抢断+拦截（可空）。

    Returns:
        标准分组或 None。
    """
    if fbref_pos is None or (isinstance(fbref_pos, float) and pd.isna(fbref_pos)):
        return None
    tokens = {t.strip().upper() for t in str(fbref_pos).replace(",", " ").split()}

    if "FW" in tokens:
        return WINGER
    if "MF" in tokens:
        kp = float(key_passes_per90) if key_passes_per90 not in (None, "") and not _isnan(key_passes_per90) else 0.0
        da = float(def_actions_per90) if def_actions_per90 not in (None, "") and not _isnan(def_actions_per90) else 0.0
        # 阈值：某一侧显著更强则判为 AM/DM，否则 CM
        if kp > da * 1.3 and kp > 0:
            return AM
        if da > kp * 1.3 and da > 0:
            return DM
        return CM
    return None


def _isnan(x) -> bool:
    try:
        return isinstance(x, float) and pd.isna(x)
    except Exception:
        return False


def assign_standard_position(
    row: pd.Series, pos_map: dict[str, str]
) -> tuple[str | None, str]:
    """对单行球员按优先级决定标准位置及其来源。

    优先级：
    1. Transfermarkt 子位置（tm_sub_position，阶段 0 补齐，最精确）
    2. Transfermarkt 主位置（tm_position，旧兼容）
    3. FBref 粗位置 + 启发式兜底

    Args:
        row: 含 ``tm_sub_position`` / ``tm_position`` / ``position``（FBref 粗位置）的行。
        pos_map: position_mapping.yaml。

    Returns:
        (标准分组或 None, 来源标记)。
    """
    # 优先 TM 子位置（更精确）
    tm_sub = map_transfermarkt_position(row.get("tm_sub_position"), pos_map)
    if tm_sub is not None:
        return tm_sub, SRC_TM

    # 回退 TM 主位置（旧兼容路径）
    tm = map_transfermarkt_position(row.get("tm_position"), pos_map)
    if tm is not None:
        return tm, SRC_TM

    guess = heuristic_position(
        row.get("position"),
        row.get("key_passes_per90"),
        row.get("def_actions_per90"),
    )
    if guess is not None:
        return guess, SRC_HEURISTIC
    return None, SRC_NONE


def add_standard_position(
    df: pd.DataFrame, pos_map: dict[str, str]
) -> pd.DataFrame:
    """给 DataFrame 增加 ``standard_position`` 与 ``position_source`` 两列。

    Args:
        df: 含 tm_position / position 等列的数据。
        pos_map: position_mapping.yaml。

    Returns:
        新增两列的**新** DataFrame。
    """
    out = df.copy()
    results = out.apply(lambda r: assign_standard_position(r, pos_map), axis=1)
    out["standard_position"] = [r[0] for r in results]
    out["position_source"] = [r[1] for r in results]
    return out
