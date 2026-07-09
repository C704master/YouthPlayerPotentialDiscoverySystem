"""年轻球员潜力发现系统 · 主入口。

阶段 0  数据采集 → 阶段 1 字段检查 → 阶段 2 数据清洗 → （后续阶段待实现）。

用法：
    python main.py                 # 运行完整管线
    python main.py --skip-collect  # 跳过数据采集（data/raw/players.csv 已存在时）
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from src import cleaner, collector, config_loader, data_loader, position_mapper

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "players.csv"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "cleaned_players.csv"


# ---------------------------------------------------------------------------
# 阶段 0 · 数据采集
# ---------------------------------------------------------------------------

def stage0_collect(config: dict) -> Path:
    """获取原始数据并存为 data/raw/players.csv。

    优先使用 Kaggle 数据集（ygtaltndg/top5-league-player-statistic），
    若不可用则尝试从缓存路径复制。返回 CSV 路径。
    """
    if RAW_CSV.exists():
        print("[阶段0] data/raw/players.csv 已存在，跳过采集。")
        return RAW_CSV

    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)

    # 尝试 1：从 Kaggle 下载
    try:
        import kagglehub

        print("[阶段0] 从 Kaggle 下载数据集...")
        kaggle_path = kagglehub.dataset_download(
            "ygtaltndg/top5-league-player-statistic"
        )
        src = Path(kaggle_path) / "Top_5_European_Leagues_2024_25_Complete_Player_Stats.csv"
        if src.exists():
            shutil.copy2(src, RAW_CSV)
            print(f"[阶段0] 已下载并保存到 {RAW_CSV}")
            return RAW_CSV
    except Exception as exc:
        print(f"[阶段0] Kaggle 下载失败: {exc}")

    # 尝试 2：从缓存查找
    cache_candidates = sorted(
        Path.home().glob(
            ".cache/kagglehub/datasets/ygtaltndg/top5-league-player-statistic/**/"
            "Top_5_European_Leagues_2024_25_Complete_Player_Stats.csv"
        ),
        reverse=True,
    )
    if cache_candidates:
        shutil.copy2(cache_candidates[0], RAW_CSV)
        print(f"[阶段0] 从缓存复制: {cache_candidates[0]}")
        return RAW_CSV

    print("[阶段0] 错误: 无法获取数据。请手动将数据集放到 data/raw/players.csv")
    sys.exit(1)


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
# 汇总输出
# ---------------------------------------------------------------------------

def summarize(df: pd.DataFrame) -> None:
    """打印清洗后的汇总统计。"""
    print("\n" + "=" * 60)
    print("清洗后数据汇总")
    print("=" * 60)
    print(f"总球员数: {len(df)}")
    print(f"联赛分布:\n{df['league'].value_counts().to_string()}")
    print(f"\n位置分布:\n{df['standard_position'].value_counts().to_string()}")
    print(f"\n位置来源:\n{df['position_source'].value_counts().to_string()}")
    print(f"\n正式评分球员数 (is_official): {df['is_official'].sum()}")
    print(f"观察名单球员数: {(~df['is_official']).sum()}")
    print(f"数据完整度均值: {df['data_completeness'].mean():.2f}")
    print(f"年龄范围: {df['age'].min():.0f} - {df['age'].max():.0f}")

    # Top 5 by 数据完整度
    print("\n数据完整度 Top 5（正式评分）:")
    official = df[df["is_official"]].nlargest(5, "data_completeness")
    for _, row in official.iterrows():
        print(
            f"  {row['player_name']:25s} | {row['standard_position']:6s} | "
            f"{row['league']:20s} | {row['age']:3.0f}岁 | "
            f"完整度 {row['data_completeness']:.2f}"
        )


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

    # 汇总
    summarize(cleaned)

    print("\n管线完成。后续阶段（评分/排名/报告）待实现。")


if __name__ == "__main__":
    main()
