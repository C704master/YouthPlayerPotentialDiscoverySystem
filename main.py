"""年轻球员潜力发现系统 · 主入口。

阶段 0  数据采集 → 阶段 1 字段检查 → 阶段 2 数据清洗 → （后续阶段待实现）。

用法：
    python main.py                 # 运行完整管线
    python main.py --skip-collect  # 跳过数据采集（data/raw/players.csv 已存在时）
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# 修复 Windows 控制台 GBK 编码对重音字符的打印问题
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src import cleaner, collector, config_loader, data_loader, feature_builder, position_mapper, scorer

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "players.csv"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "cleaned_players.csv"
SCORED_CSV = PROJECT_ROOT / "data" / "processed" / "scored_players.csv"
_FBREF_DATASET = "emrey3lmaz/top-5-league-football-player-stats-2017-2025"
_TM_DATASET = "davidcariboo/player-scores"
_FIFA_DATASET = "jacksonjohannessen/fifa-and-irl-soccer-player-data"


# ---------------------------------------------------------------------------
# 阶段 0 · 数据采集
# ---------------------------------------------------------------------------

def _download_kaggle(handle: str) -> Path:
    """下载 Kaggle 数据集，返回所在目录路径。"""
    import kagglehub

    print(f"  从 Kaggle 下载 {handle}...")
    return Path(kagglehub.dataset_download(handle))


def _cache_lookup(handle: str, filename: str) -> Path | None:
    """从本地缓存查找已下载的数据集文件。"""
    dir_pattern = handle.replace("/", "/")
    candidates = sorted(
        Path.home().glob(f".cache/kagglehub/datasets/{dir_pattern}/**/{filename}"),
        reverse=True,
    )
    return candidates[0] if candidates else None


def stage0_collect(config: dict) -> Path:
    """获取 FBref 原始数据 + Transfermarkt 补充数据 → data/raw/players.csv。

    数据集：
    - FBref: emrey3lmaz/top-5-league-football-player-stats-2017-2025（178 列）
    - TM:    davidcariboo/player-scores（身高、身价、详细位置）

    返回 CSV 路径。
    """
    if RAW_CSV.exists():
        print("[阶段0] data/raw/players.csv 已存在，跳过采集。")
        return RAW_CSV

    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)

    # --- FBref 数据 ---
    try:
        fbref_dir = _download_kaggle(_FBREF_DATASET)
    except Exception:
        cached = _cache_lookup(
            _FBREF_DATASET, "Top5_League_Players_2017to2024_dataset.csv"
        )
        if cached:
            fbref_dir = cached.parent
        else:
            print("[阶段0] 错误: 无法获取 FBref 数据集。")
            sys.exit(1)

    fbref_src = fbref_dir / "Top5_League_Players_2017to2024_dataset.csv"
    if not fbref_src.exists():
        alt = _cache_lookup(_FBREF_DATASET, "Top5_League_Players_2017to2024_dataset.csv")
        if alt:
            fbref_src = alt

    df_fbref = pd.read_csv(fbref_src, sep=";")
    df_fbref = df_fbref[df_fbref["season"] == 2425].copy()  # 只取 2024-25
    print(f"[阶段0] FBref 2024-25: {len(df_fbref)} 名球员")

    # --- Transfermarkt 数据 ---
    try:
        tm_dir = _download_kaggle(_TM_DATASET)
    except Exception:
        cached = _cache_lookup(_TM_DATASET, "players.csv")
        if cached:
            tm_dir = cached.parent
        else:
            print("[阶段0] 警告: 无法获取 Transfermarkt 数据，跳过 TM 补充。")
            df_fbref.to_csv(RAW_CSV, index=False)
            return RAW_CSV

    tm_src = tm_dir / "players.csv"
    df_tm = pd.read_csv(tm_src)
    print(f"[阶段0] Transfermarkt: {len(df_tm):,} 名球员")

    # --- 匹配 ---
    df_merged = collector.attach_transfermarkt_data(df_fbref, df_tm)
    matched = df_merged["height"].notna().sum()
    print(f"[阶段0] TM 匹配成功: {matched} ({matched / len(df_merged) * 100:.1f}%)")

    # --- FIFA 数据（体重） ---
    try:
        fifa_dir = _download_kaggle(_FIFA_DATASET)
        fifa_src = fifa_dir / "fifa_fbref_merged.csv"
        df_fifa = pd.read_csv(fifa_src, low_memory=False)
        print(f"[阶段0] FIFA: {len(df_fifa):,} 名球员")
        df_merged = collector.attach_fifa_data(df_merged, df_fifa)
        w_matched = df_merged["weight"].notna().sum()
        print(f"[阶段0] FIFA 匹配成功: {w_matched} ({w_matched / len(df_merged) * 100:.1f}%)")
    except Exception as exc:
        print(f"[阶段0] 警告: 无法获取 FIFA 数据 ({exc})，跳过体重补充。")

    df_merged.to_csv(RAW_CSV, index=False)
    print(f"[阶段0] 已保存到 {RAW_CSV}")
    return RAW_CSV


# ---------------------------------------------------------------------------
# 阶段 1 · 数据读取与字段检查
# ---------------------------------------------------------------------------

def stage1_load_and_check() -> tuple[pd.DataFrame, data_loader.FieldReport]:
    """读取数据 + 字段映射 + 字段检查报告。"""
    field_mapping = config_loader.load_config("field_mapping.yaml")
    df, report = data_loader.load_players(RAW_CSV, field_mapping)
    print("\n[阶段1] 字段检查报告:")
    print(data_loader.format_report(report))
    return df, report


# ---------------------------------------------------------------------------
# 阶段 2 · 数据清洗与位置映射
# ---------------------------------------------------------------------------

def stage2_clean(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """清洗 + 位置映射 + 筛选。"""
    pos_mapping = config_loader.load_config("position_mapping.yaml")
    league_mapping = config_loader.load_config("league_mapping.yaml")
    scoring_positions = {"Winger", "AM", "CM", "DM"}

    # 联赛名归一化（供阶段 5 Opta 强度表匹配）
    if "league" in df.columns:
        df = df.copy()
        df["league"] = df["league"].apply(
            lambda n: collector.normalize_league_name(n, league_mapping)
        )

    cleaned = cleaner.clean(
        df,
        pos_map=pos_mapping,
        max_age=config.get("filters", {}).get("max_age", 21),
        min_minutes=config.get("filters", {}).get("min_minutes", 600),
        scoring_positions=scoring_positions,
        ref=date(2026, 1, 1),  # 固定参考日期，保证可复现
    )

    PROCESSED_CSV.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(PROCESSED_CSV, index=False)
    print(f"\n[阶段2] 清洗后数据写入 {PROCESSED_CSV}")
    return cleaned


# ---------------------------------------------------------------------------
# 阶段 3 · 特征计算
# ---------------------------------------------------------------------------


def stage3_build_features(df: pd.DataFrame) -> pd.DataFrame:
    """计算 per90 指标，输出增强特征 DataFrame。"""
    feats = feature_builder.build_features(df)
    per90_cols = [c for c in feats.columns if c.endswith("_per90")]
    print(f"\n[阶段3] 已计算 {len(per90_cols)} 个 per90 派生字段")
    return feats


# ---------------------------------------------------------------------------
# 阶段 4 · 潜力评分
# ---------------------------------------------------------------------------


def stage4_score(df: pd.DataFrame) -> pd.DataFrame:
    """分位置计算 0-100 潜力评分（含联赛强度修正）。"""
    weights_cfg = config_loader.load_config("scoring_weights.yaml")
    strength_cfg = config_loader.load_config("league_strength_opta.yaml")
    strength_map = {str(k): float(v) for k, v in strength_cfg.get("leagues", {}).items()}
    scored = scorer.score_players(df, weights_cfg, league_strength_map=strength_map)
    scored.to_csv(SCORED_CSV, index=False)
    print(f"[阶段4] 评分结果写入 {SCORED_CSV}")
    return scored


# ---------------------------------------------------------------------------
# 汇总输出
# ---------------------------------------------------------------------------


def summarize(cleaned: pd.DataFrame, scored: pd.DataFrame) -> None:
    """打印清洗和评分后的汇总统计。"""
    print("\n" + "=" * 60)
    print("清洗后数据汇总")
    print("=" * 60)
    print(f"总球员数: {len(cleaned)}")
    print(f"联赛分布:\n{cleaned['league'].value_counts().to_string()}")
    print(f"\n位置分布:\n{cleaned['standard_position'].value_counts().to_string()}")
    print(f"\n位置来源:\n{cleaned['position_source'].value_counts().to_string()}")
    print(f"\n正式评分球员数 (is_official): {cleaned['is_official'].sum()}")
    print(f"观察名单球员数: {(~cleaned['is_official']).sum()}")

    # 评分汇总
    official = scored[scored["is_official"] == True]
    print("\n" + "=" * 60)
    print("评分汇总（正式评分球员）")
    print("=" * 60)
    print(f"平均分: {official['total_score'].mean():.1f}")
    print(f"最高分: {official['total_score'].max():.1f}")
    print(f"最低分: {official['total_score'].min():.1f}")

    # --- 排行榜 ---
    print("\n" + "=" * 60)
    print("潜力榜 Top 20（正式评分）")
    print("=" * 60)
    top20 = official.nlargest(20, "total_score")
    for rank, (_, r) in enumerate(top20.iterrows(), 1):
        print(
            f"  {rank:2d}. {r['player_name']:28s} | {r['standard_position']:6s} | "
            f"{r['league']:20s} | {r['age']:3.0f}岁 | "
            f"总分 {r['total_score']:5.1f} | "
            f"核心 {r['core_performance']:5.1f} | "
            f"行为 {r['behavior_score']:5.1f}"
        )

    # --- 分位置 Top 5 ---
    for pos in ["Winger", "AM", "CM", "DM"]:
        sub = official[official["standard_position"] == pos]
        if len(sub) == 0:
            continue
        print(f"\n--- {pos} Top 5 ---")
        for rank, (_, r) in enumerate(sub.nlargest(5, "total_score").iterrows(), 1):
            print(
                f"  {rank}. {r['player_name']:28s} | {r['league']:20s} | "
                f"{r['age']:.0f}岁 | 总分 {r['total_score']:.1f}"
            )
    print()


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="年轻球员潜力发现系统")
    parser.add_argument(
        "--skip-collect",
        action="store_true",
        help="跳过数据采集（data/raw/players.csv 已存在时）",
    )
    args = parser.parse_args()

    config = config_loader.load_config("config.yaml")

    # 阶段 0
    if not args.skip_collect or not RAW_CSV.exists():
        stage0_collect(config)
    else:
        print("[阶段0] 跳过采集（--skip-collect 且文件已存在）。")

    # 阶段 1
    df, report = stage1_load_and_check()
    if not report.can_analyze:
        print("\n[阶段1] 错误: 数据不满足正式分析条件，请检查数据源。")
        sys.exit(1)

    # 阶段 2
    cleaned = stage2_clean(df, config)

    # 阶段 3
    feats = stage3_build_features(cleaned)

    # 阶段 4
    scored = stage4_score(feats)

    # 汇总
    summarize(cleaned, scored)


if __name__ == "__main__":
    main()
