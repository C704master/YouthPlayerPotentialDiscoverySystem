"""阶段 0 · 数据采集与位置补充（方案 B）。

设计原则：把**纯数据处理逻辑**（可离线测试）与**网络抓取**（薄封装、惰性导入 ScraperFC）
彻底分离。前者是本模块的主体并有完整单测覆盖；后者只是把 ScraperFC 的返回喂给纯函数。

参见 docs/阶段0-数据采集与位置补充.md 与 F&Q/方案B-数据采集实现思路.md。
"""
from __future__ import annotations

import unicodedata
from typing import Iterable

import pandas as pd

# ----------------------------------------------------------------------------
# 纯函数：可完全离线测试
# ----------------------------------------------------------------------------


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """把 FBref 的两级表头（MultiIndex columns）扁平化为一级列名。

    规则：
    - 顶层为 ``Unnamed...`` 或空 → 只取底层名（如 ``Player``）。
    - 顶层有意义且与底层不同 → 拼成 ``顶层_底层``（如 ``Per 90 Minutes_Gls``），
      以区分 ``Performance_Gls`` 与 ``Per 90 Minutes_Gls`` 这类重名。
    - 已是一级列名 → 原样保留。

    Args:
        df: 可能带两级表头的 DataFrame。

    Returns:
        列名扁平化后的**新** DataFrame（不修改入参）。
    """
    out = df.copy()
    new_cols: list[str] = []
    for col in out.columns:
        if isinstance(col, tuple):
            top = str(col[0]).strip()
            bottom = str(col[-1]).strip()
            if top.lower().startswith("unnamed") or top == "":
                new_cols.append(bottom)
            elif top.lower() == bottom.lower():
                new_cols.append(bottom)
            else:
                new_cols.append(f"{top}_{bottom}")
        else:
            new_cols.append(str(col).strip())
    out.columns = new_cols
    return out


def normalize_league_name(name: str, mapping: dict[str, str]) -> str:
    """把采集源的联赛名归一化为 Opta 强度表使用的 key。

    大小写不敏感；未在映射表中的名称原样返回（去空格）。

    Args:
        name: 原始联赛名（如 FBref 的 ``"EPL"``）。
        mapping: 归一化映射（来自 config/league_mapping.yaml）。

    Returns:
        归一化后的联赛名（如 ``"Premier League"``）。
    """
    if name is None:
        return name
    key = str(name).strip()
    lowered = {k.lower(): v for k, v in mapping.items()}
    return lowered.get(key.lower(), key)


def merge_stat_categories(
    frames: Iterable[pd.DataFrame], key: str = "player_id"
) -> pd.DataFrame:
    """把同一联赛×赛季的多个 stat 分类 DataFrame 按球员键横向合并成一行/球员。

    - 先丢弃各表内部的重复列。
    - 合并时只带入目标表中尚不存在的新列（除了连接键），避免列爆炸/重名。

    Args:
        frames: 若干已扁平化、含 ``key`` 列的 DataFrame。
        key: 连接键（默认 ``player_id``）。

    Returns:
        合并后的单个 DataFrame。

    Raises:
        ValueError: frames 为空，或某个表缺少连接键。
    """
    frames = list(frames)
    if not frames:
        raise ValueError("merge_stat_categories: frames 不能为空")

    merged: pd.DataFrame | None = None
    for df in frames:
        if key not in df.columns:
            raise ValueError(f"merge_stat_categories: 表缺少连接键 '{key}'")
        df = df.loc[:, ~df.columns.duplicated()]
        if merged is None:
            merged = df.copy()
        else:
            new_cols = [c for c in df.columns if c == key or c not in merged.columns]
            merged = merged.merge(df[new_cols], on=key, how="outer")
    return merged


def norm_name(s: str) -> str:
    """把姓名/球队名归一化用于跨源匹配：去重音、小写、去多余标点与空格。

    Args:
        s: 原始字符串。

    Returns:
        归一化后的字符串；``None``/空返回空串。
    """
    if s is None:
        return ""
    text = unicodedata.normalize("NFKD", str(s))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace(".", "").replace("-", " ")
    return " ".join(text.split())


def _match_key(name: str, team: str) -> str:
    return f"{norm_name(name)}|{norm_name(team)}"


def attach_position(
    fbref_df: pd.DataFrame,
    tm_df: pd.DataFrame,
    name_col: str = "player_name",
    team_col: str = "team",
    tm_name_col: str = "player_name",
    tm_team_col: str = "team",
    tm_pos_col: str = "position",
) -> pd.DataFrame:
    """把 Transfermarkt 主位置按 ``姓名+球队`` 模糊匹配挂到 FBref 数据上。

    在结果中新增 ``tm_position`` 列（匹配不上为 NaN，供阶段 2 回落启发式）。

    Args:
        fbref_df: FBref 侧数据（每行一名球员）。
        tm_df: Transfermarkt 侧数据（含主位置）。
        name_col/team_col: FBref 侧姓名/球队列名。
        tm_name_col/tm_team_col/tm_pos_col: TM 侧姓名/球队/主位置列名。

    Returns:
        新增 ``tm_position`` 列的**新** DataFrame。
    """
    left = fbref_df.copy()
    left["_k"] = [
        _match_key(n, t) for n, t in zip(left[name_col], left[team_col])
    ]

    right = tm_df.copy()
    right["_k"] = [
        _match_key(n, t) for n, t in zip(right[tm_name_col], right[tm_team_col])
    ]
    right = right[["_k", tm_pos_col]].rename(columns={tm_pos_col: "tm_position"})
    right = right.drop_duplicates("_k", keep="first")

    merged = left.merge(right, on="_k", how="left").drop(columns=["_k"])
    return merged


def attach_transfermarkt_data(
    fbref_df: pd.DataFrame,
    tm_df: pd.DataFrame,
    name_col: str = "player",
    tm_name_col: str = "name",
) -> pd.DataFrame:
    """把 Transfermarkt 数据（位置、身高、身价）按球员姓名模糊匹配到 FBref 数据。

    TM 俱乐部名使用德语全名（如 "1. Fußball-Club Köln"），与 FBref 英文短名（"Köln"）
    几乎无交集。因此采用**纯姓名匹配**（去重音、小写、去标点）。

    Args:
        fbref_df: FBref 侧数据。
        tm_df: Transfermarkt 侧数据（含 sub_position, height_in_cm, market_value_in_eur）。
        name_col: FBref 侧姓名列名。
        tm_name_col: TM 侧姓名列名。

    Returns:
        新增 ``tm_sub_position`` / ``height`` / ``market_value`` 列的**新** DataFrame。
    """
    left = fbref_df.copy()
    left["_nk"] = left[name_col].apply(norm_name)

    right = tm_df.copy()
    right["_nk"] = right[tm_name_col].apply(norm_name)

    # 需要的列：姓名键 + TM 位置 + 身高 + 身价
    keep_cols = ["_nk"]
    col_rename: dict[str, str] = {}
    if "sub_position" in right.columns:
        keep_cols.append("sub_position")
        col_rename["sub_position"] = "tm_sub_position"
    if "height_in_cm" in right.columns:
        keep_cols.append("height_in_cm")
        col_rename["height_in_cm"] = "height"
    if "market_value_in_eur" in right.columns:
        keep_cols.append("market_value_in_eur")
        col_rename["market_value_in_eur"] = "market_value"

    right = right[keep_cols].rename(columns=col_rename)
    # 同名球员保留第一条（最新的，TM 数据按 last_season 排序）
    right = right.drop_duplicates("_nk", keep="first")

    merged = left.merge(right, on="_nk", how="left").drop(columns=["_nk"])
    return merged


def finalize_raw(df: pd.DataFrame, league: str, season: str,
                 league_mapping: dict[str, str]) -> pd.DataFrame:
    """给合并后的球员数据补上归一化的 league/season 列（阶段 5 需要）。

    Args:
        df: 合并后的球员 DataFrame。
        league: 原始联赛名。
        season: 赛季字符串。
        league_mapping: 联赛名归一化映射。

    Returns:
        新增/覆盖 ``league``、``season`` 列的**新** DataFrame。
    """
    out = df.copy()
    out["league"] = normalize_league_name(league, league_mapping)
    out["season"] = season
    return out


# ----------------------------------------------------------------------------
# 网络抓取薄封装：惰性导入 ScraperFC；离线测试通过 mock 覆盖
# ----------------------------------------------------------------------------


def scrape_fbref_stats(season: str, league: str, categories: Iterable[str],
                       wait_time: int = 7) -> dict[str, pd.DataFrame]:
    """抓取单个联赛×赛季的多个 stat 分类，返回 {分类: player_stats}。

    仅在真实抓取时调用。ScraperFC 惰性导入，避免离线测试/管道逻辑依赖它。

    Args:
        season: FBref 赛季格式，如 ``"2024-2025"``。
        league: FBref 联赛名，如 ``"EPL"``。
        categories: 需要的 stat 分类列表。
        wait_time: 请求间隔秒数（限速，FBref 每分钟 ≤10 次）。

    Returns:
        ``{分类名: 已扁平化的 player_stats DataFrame}``。
    """
    from ScraperFC.fbref import FBref  # 惰性导入

    fb = FBref(wait_time=wait_time)
    result: dict[str, pd.DataFrame] = {}
    for cat in categories:
        _squad, _opp, players = fb.scrape_stats(season, league, cat)
        result[cat] = flatten_columns(players)
    return result


def scrape_transfermarkt_players(season: str, league: str) -> pd.DataFrame:
    """抓取单个联赛×赛季的 Transfermarkt 球员（含主位置）。

    Args:
        season: Transfermarkt 赛季格式，如 ``"24/25"``。
        league: Transfermarkt 联赛名，如 ``"EPL"``。

    Returns:
        含主位置的球员 DataFrame。
    """
    import ScraperFC as sfc  # 惰性导入

    tm = sfc.Transfermarkt()
    return tm.scrape_players(season, league)
