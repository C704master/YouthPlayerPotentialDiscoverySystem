"""阶段 1 · 数据读取与字段检查。

读取 data/raw/players.csv，用 field_mapping 把外部列名归一化为内部标准字段名，
并按「必须 / 核心评分 / 增强」三级字段生成检查报告。

参见 docs/阶段1-数据读取与字段检查.md。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# 三级字段清单（内部标准名）
REQUIRED_FIELDS = ["player_name", "position", "team", "league", "minutes"]
# 年龄二选一：age 或 date_of_birth 至少有其一
AGE_FIELDS = ["age", "date_of_birth"]
CORE_FIELDS = [
    "goals", "assists", "shots", "key_passes", "dribbles",
    "passes", "tackles", "interceptions", "yellow_cards", "red_cards",
]
ENHANCE_FIELDS = [
    "xg", "xa", "market_value", "height", "weight",
    "progressive_carries", "shot_creating_actions",
]


def invert_field_mapping(mapping: dict[str, list[str]]) -> dict[str, str]:
    """把 {标准名: [别名...]} 反转为 {别名小写: 标准名}，供列名归一化查表。

    Args:
        mapping: field_mapping.yaml 解析结果。

    Returns:
        别名（小写）到标准字段名的映射。
    """
    alias_to_std: dict[str, str] = {}
    for std, aliases in mapping.items():
        # 标准名本身也算别名
        alias_to_std[std.lower()] = std
        for alias in aliases or []:
            alias_to_std[str(alias).lower()] = std
    return alias_to_std


def apply_field_mapping(df: pd.DataFrame, mapping: dict[str, list[str]]) -> pd.DataFrame:
    """把 DataFrame 的外部列名按映射改成内部标准字段名。

    未在映射中的列保持原样。多个外部列映射到同一标准名时，保留第一个。

    Args:
        df: 原始 DataFrame。
        mapping: field_mapping.yaml 解析结果。

    Returns:
        列名归一化后的**新** DataFrame。
    """
    alias_to_std = invert_field_mapping(mapping)
    rename: dict[str, str] = {}
    taken: set[str] = set()
    for col in df.columns:
        std = alias_to_std.get(str(col).lower())
        if std and std not in taken:
            rename[col] = std
            taken.add(std)
    return df.rename(columns=rename)


@dataclass
class FieldReport:
    """字段检查结果。"""

    n_rows: int
    present_required: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    has_age: bool = False
    present_core: list[str] = field(default_factory=list)
    missing_core: list[str] = field(default_factory=list)
    present_enhance: list[str] = field(default_factory=list)
    missing_enhance: list[str] = field(default_factory=list)

    @property
    def can_analyze(self) -> bool:
        """是否具备正式分析的最低条件：必须字段齐全且有年龄信息。"""
        return not self.missing_required and self.has_age


def check_fields(df: pd.DataFrame) -> FieldReport:
    """按三级字段清单检查 DataFrame，生成 FieldReport。

    Args:
        df: 已做列名归一化的 DataFrame。

    Returns:
        FieldReport 实例。
    """
    cols = set(df.columns)

    present_req = [f for f in REQUIRED_FIELDS if f in cols]
    missing_req = [f for f in REQUIRED_FIELDS if f not in cols]
    has_age = any(f in cols for f in AGE_FIELDS)

    return FieldReport(
        n_rows=len(df),
        present_required=present_req,
        missing_required=missing_req,
        has_age=has_age,
        present_core=[f for f in CORE_FIELDS if f in cols],
        missing_core=[f for f in CORE_FIELDS if f not in cols],
        present_enhance=[f for f in ENHANCE_FIELDS if f in cols],
        missing_enhance=[f for f in ENHANCE_FIELDS if f not in cols],
    )


def format_report(report: FieldReport) -> str:
    """把 FieldReport 格式化为可打印的多行字符串（对应验收标准的控制台输出）。"""
    lines = [
        f"读取行数: {report.n_rows}",
        f"必须字段 齐全: {'是' if not report.missing_required else '否'}"
        f"（缺失: {report.missing_required or '无'}）",
        f"年龄信息: {'有' if report.has_age else '无（age/date_of_birth 均缺失）'}",
        f"核心评分字段 缺失: {report.missing_core or '无'}",
        f"增强字段 缺失: {report.missing_enhance or '无'}",
        f"可正式分析: {'是' if report.can_analyze else '否'}",
    ]
    if report.missing_required or not report.has_age:
        lines.append("⚠ 警告: 必须字段/年龄不完整，可能无法进入正式分析。")
    return "\n".join(lines)


def load_players(
    csv_path: str | Path, mapping: dict[str, list[str]]
) -> tuple[pd.DataFrame, FieldReport]:
    """读取 CSV，做列名归一化并返回 (DataFrame, 字段检查报告)。

    Args:
        csv_path: players.csv 路径。
        mapping: field_mapping.yaml 解析结果。

    Returns:
        (归一化后的 DataFrame, FieldReport)。

    Raises:
        FileNotFoundError: CSV 不存在。
    """
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"数据文件不存在: {p}")
    df = pd.read_csv(p)
    df = apply_field_mapping(df, mapping)
    report = check_fields(df)
    return df, report
