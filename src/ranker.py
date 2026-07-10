"""阶段 6 · 候选清单与排行榜。

从评分结果生成：
- 100 名候选球员清单（CSV + Excel）
- Top 20 潜力排行榜（CSV + Excel + Markdown）
- 分位置 / 分联赛排行榜

参见 docs/阶段6-候选清单与排行榜.md。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# 候选清单输出列
_CANDIDATE_COLS = [
    "player_name", "age", "standard_position", "team", "league",
    "minutes", "total_score", "data_completeness", "market_value",
    "position_source",
]

# 排行榜输出列
_RANKING_COLS = [
    "player_name", "age", "standard_position", "team", "league",
    "minutes", "total_score", "core_performance", "behavior_score",
    "age_score", "reliability_score", "league_score", "risk_penalty",
    "data_completeness", "market_value", "height",
]


def generate_candidates(df: pd.DataFrame, output_dir: str | Path,
                        top_n: int = 100) -> pd.DataFrame:
    """生成候选球员清单（正式评分球员按 total_score 降序取前 N）。

    Args:
        df: 含 total_score 的评分 DataFrame。
        output_dir: 输出目录。
        top_n: 取前 N 名（默认 100）。

    Returns:
        候选球员 DataFrame。
    """
    official = df[df["is_official"] == True].copy()
    candidates = official.nlargest(top_n, "total_score").reset_index(drop=True)
    candidates.insert(0, "rank", range(1, len(candidates) + 1))

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # CSV
    cols = ["rank"] + [c for c in _CANDIDATE_COLS if c in candidates.columns]
    csv_path = out / "candidate_players_100.csv"
    candidates[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Excel
    xlsx_path = out / "candidate_players_100.xlsx"
    candidates[cols].to_excel(xlsx_path, index=False, engine="openpyxl")

    print(f"[阶段6] 候选清单 ({len(candidates)} 人) → {csv_path}")
    return candidates


def generate_rankings(df: pd.DataFrame, output_dir: str | Path,
                      top_n: int = 20) -> pd.DataFrame:
    """生成 Top N 潜力排行榜（CSV + Excel + Markdown）。

    Args:
        df: 含 total_score 的评分 DataFrame。
        output_dir: 输出目录。
        top_n: 排行榜人数（默认 20）。

    Returns:
        排行榜 DataFrame。
    """
    official = df[df["is_official"] == True].copy()
    ranking = official.nlargest(top_n, "total_score").reset_index(drop=True)
    ranking.insert(0, "rank", range(1, len(ranking) + 1))

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # CSV
    cols = ["rank"] + [c for c in _RANKING_COLS if c in ranking.columns]
    csv_path = out / "top20_ranking.csv"
    ranking[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Excel
    xlsx_path = out / "top20_ranking.xlsx"
    ranking[cols].to_excel(xlsx_path, index=False, engine="openpyxl")

    print(f"[阶段6] 排行榜 Top {top_n} → {csv_path}")

    # Markdown
    md_path = out / "top20_ranking.md"
    _write_ranking_md(ranking, md_path)
    print(f"[阶段6] 排行榜 Markdown → {md_path}")

    return ranking


def _write_ranking_md(ranking: pd.DataFrame, path: Path) -> None:
    """把排行榜写成 Markdown 表格。"""
    lines = [
        "# 年轻球员潜力排行榜 Top 20",
        "",
        f"> 自动生成于 2026-07-10。基于 per90 效率数据 + Opta 联赛强度修正。",
        "",
        "| # | 球员 | 位置 | 联赛 | 年龄 | 总分 | 核心 | 行为 | 年龄分 | 联赛分 | 风险 |",
        "|---|------|------|------|------|------|------|------|--------|--------|------|",
    ]
    for _, r in ranking.iterrows():
        lines.append(
            f"| {int(r['rank'])} | {r['player_name']} | {r['standard_position']} | "
            f"{r['league']} | {int(r['age'])} | {r['total_score']:.1f} | "
            f"{r['core_performance']:.1f} | {r['behavior_score']:.1f} | "
            f"{r['age_score']:.0f} | {r['league_score']:.0f} | "
            f"{r['risk_penalty']:.0f} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_position_rankings(df: pd.DataFrame, output_dir: str | Path) -> dict:
    """分位置 Top 10 排行榜。

    Returns:
        {位置名: DataFrame} 字典。
    """
    official = df[df["is_official"] == True].copy()
    results = {}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for pos in ["Winger", "AM", "CM", "DM"]:
        sub = official[official["standard_position"] == pos]
        if len(sub) == 0:
            continue
        ranking = sub.nlargest(10, "total_score").reset_index(drop=True)
        ranking.insert(0, "rank", range(1, len(ranking) + 1))
        cols = ["rank"] + [c for c in _RANKING_COLS if c in ranking.columns]
        csv_path = out / f"top10_{pos}.csv"
        ranking[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")
        results[pos] = ranking
        print(f"[阶段6] {pos} Top 10 → {csv_path}")

    return results


def generate_league_rankings(df: pd.DataFrame, output_dir: str | Path) -> dict:
    """分联赛 Top 5 排行榜。

    Returns:
        {联赛名: DataFrame} 字典。
    """
    official = df[df["is_official"] == True].copy()
    results = {}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for league in official["league"].unique():
        sub = official[official["league"] == league]
        if len(sub) == 0:
            continue
        ranking = sub.nlargest(5, "total_score").reset_index(drop=True)
        ranking.insert(0, "rank", range(1, len(ranking) + 1))
        cols = ["rank"] + [c for c in _RANKING_COLS if c in ranking.columns]
        safe_name = league.replace(" ", "_")
        csv_path = out / f"top5_{safe_name}.csv"
        ranking[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")
        results[league] = ranking

    print(f"[阶段6] 分联赛 Top 5 ({len(results)} 个联赛)")
    return results


def build_observation_list(df: pd.DataFrame, output_dir: str | Path,
                           max_age: int = 21) -> pd.DataFrame:
    """观察名单：分钟不足但年龄小的潜力股。

    Args:
        df: 评分 DataFrame。
        output_dir: 输出目录。
        max_age: 最大年龄（出场不足但年轻）。

    Returns:
        观察名单 DataFrame。
    """
    obs = df[
        (df["is_official"] == False) & (df["age"] <= max_age)
    ].copy()
    obs = obs.nlargest(30, "total_score").reset_index(drop=True)
    obs.insert(0, "rank", range(1, len(obs) + 1))

    out = Path(output_dir)
    cols = ["rank"] + [c for c in _CANDIDATE_COLS if c in obs.columns]
    csv_path = out / "observation_list.csv"
    obs[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[阶段6] 观察名单 ({len(obs)} 人) → {csv_path}")

    return obs
