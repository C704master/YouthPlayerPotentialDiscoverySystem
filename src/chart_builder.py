"""阶段 7 · 雷达图。

为正式评分球员生成能力结构雷达图（PNG）。
每张图的坐标轴为该球员位置的评分指标百分位值。
参见 docs/阶段7-雷达图.md。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # 无 GUI 后端

# 雷达图尺寸
_FIG_SIZE = (6, 6)
_DPI = 120

# 分位置雷达图坐标轴（显示名 → DataFrame 列名）
_RADAR_AXES = {
    "Winger": {
        "Gls/90": "goals_per90",
        "Ast/90": "assists_per90",
        "Shots/90": "shots_per90",
        "KP/90": "key_passes_per90",
        "Drib/90": "dribbles_per90",
        "PrgC/90": "progressive_carries_per90",
        "SCA/90": "shot_creating_actions_per90",
        "xG/90": "xg_per90",
    },
    "AM": {
        "Ast/90": "assists_per90",
        "KP/90": "key_passes_per90",
        "SCA/90": "shot_creating_actions_per90",
        "Pass/90": "passes_per90",
        "PrgC/90": "progressive_carries_per90",
        "xA/90": "xa_per90",
        "Shots/90": "shots_per90",
        "Drib/90": "dribbles_per90",
    },
    "CM": {
        "Pass/90": "passes_per90",
        "KP/90": "key_passes_per90",
        "Tkl/90": "tackles_per90",
        "Int/90": "interceptions_per90",
        "PrgC/90": "progressive_carries_per90",
        "SCA/90": "shot_creating_actions_per90",
        "Gls/90": "goals_per90",
        "xG/90": "xg_per90",
    },
    "DM": {
        "Tkl/90": "tackles_per90",
        "Int/90": "interceptions_per90",
        "Def/90": "def_actions_per90",
        "Pass/90": "passes_per90",
        "KP/90": "key_passes_per90",
        "PrgC/90": "progressive_carries_per90",
        "Blocks/90": "blocks_per90",
        "Discipline": "yellow_cards_per90",
    },
}


def _safe_filename_part(value: object) -> str:
    return str(value or "unknown").replace("/", "_").replace("\\", "_").strip()


def _compute_percentiles(player: pd.Series, group: pd.DataFrame,
                         axes: dict[str, str]) -> list[float]:
    """计算球员在各雷达轴上的同位置百分位值。"""
    values = []
    for _label, col in axes.items():
        if col not in group.columns:
            values.append(50.0)
            continue
        raw = pd.to_numeric(group[col], errors="coerce").fillna(0)
        player_val = pd.to_numeric(player.get(col, 0), errors="coerce") or 0.0
        pct = (raw < player_val).sum() / max(len(raw), 1) * 100
        # 纪律类指标反向
        if col in ("yellow_cards_per90", "red_cards_per90"):
            pct = 100 - pct
        values.append(round(pct, 1))
    return values


def _draw_radar(values: list[float], labels: list[str], title: str,
                save_path: Path) -> None:
    """绘制单张雷达图并保存为 PNG。"""
    n = len(values)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=_FIG_SIZE, subplot_kw={"projection": "polar"})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # 刻度与网格
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=6)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.grid(True, linestyle="--", alpha=0.4)

    # 填充
    ax.fill(angles_closed, values_closed, alpha=0.25, color="#2196F3")
    ax.plot(angles_closed, values_closed, linewidth=2, color="#1565C0")

    # 数值标注
    for angle, val in zip(angles, values):
        ax.annotate(f"{val:.0f}", xy=(angle, val + 4), fontsize=7,
                    ha="center", va="center", color="#333")

    ax.set_title(title, fontsize=11, fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(save_path, dpi=_DPI, bbox_inches="tight")
    plt.close(fig)


def generate_radar_charts(df: pd.DataFrame, output_dir: str | Path,
                          top_n: int | None = None) -> list[Path]:
    """为正式评分球员生成雷达图 PNG。

    Args:
        df: 含 per90 列 + standard_position + total_score 的评分 DataFrame。
        output_dir: PNG 输出目录。
        top_n: 可选生成前 N 名；None 表示生成全部正式评分球员。

    Returns:
        已生成的 PNG 文件路径列表。
    """
    official = df[df["is_official"] == True].copy()
    top_players = (
        official.nlargest(top_n, "total_score")
        if top_n
        else official.sort_values("total_score", ascending=False)
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    duplicate_names = set(official.loc[official["player_name"].duplicated(keep=False), "player_name"])

    for _, player in top_players.iterrows():
        pos = player.get("standard_position", "Winger")
        axes = _RADAR_AXES.get(pos, _RADAR_AXES["Winger"])
        group = official[official["standard_position"] == pos]

        values = _compute_percentiles(player, group, axes)
        labels = list(axes.keys())
        title = f"{player['player_name']} ({pos}, {int(player['age'])}yr)"

        # 同名球员/同一球员跨队记录用球队补充，避免 PNG 覆盖。
        safe_name = _safe_filename_part(player["player_name"])
        if player["player_name"] in duplicate_names:
            safe_name = f"{safe_name}_{_safe_filename_part(player.get('team'))}"
        save_path = out / f"{safe_name}_radar.png"
        _draw_radar(values, labels, title, save_path)
        generated.append(save_path)

    print(f"[阶段7] 已生成 {len(generated)} 张雷达图 -> {out}")
    return generated
