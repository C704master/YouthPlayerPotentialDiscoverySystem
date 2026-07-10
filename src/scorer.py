"""阶段 4 · 潜力评分模型。

分位置（Winger/AM/CM/DM）计算 0-100 分潜力评分。
参见 docs/阶段4-潜力评分模型.md。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# 标准分组
_WINGER, _AM, _CM, _DM = "Winger", "AM", "CM", "DM"
_STANDARD_GROUPS = {_WINGER, _AM, _CM, _DM}


# ---------------------------------------------------------------------------
# 百分位计算（同位置内部排名）
# ---------------------------------------------------------------------------


def _percentile_rank(series: pd.Series) -> pd.Series:
    """计算 Series 内每个值的百分位（0-100），NaN 返回 50（中位）。"""
    result = series.rank(pct=True) * 100
    return result.fillna(50)


def _safe_pct(df: pd.DataFrame, col: str) -> pd.Series:
    """对 DataFrame 的单列计算百分位，缺失列返回全 50。"""
    if col not in df.columns:
        return pd.Series([50.0] * len(df), index=df.index)
    return _percentile_rank(pd.to_numeric(df[col], errors="coerce"))


# ---------------------------------------------------------------------------
# 年龄评分
# ---------------------------------------------------------------------------


def score_age(age: pd.Series, min_age: int = 15, max_age: int = 21,
              age_15_score: float = 100, age_21_score: float = 60) -> pd.Series:
    """年龄优势分：越年轻越高。线性插值。"""
    age = pd.to_numeric(age, errors="coerce").fillna(max_age)
    clamped = age.clip(min_age, max_age)
    return age_15_score - (clamped - min_age) / (max_age - min_age) * (age_15_score - age_21_score)


# ---------------------------------------------------------------------------
# 出场可靠性评分
# ---------------------------------------------------------------------------


def score_reliability(minutes: pd.Series, min_minutes: int = 600, min_score: float = 50,
                      full_minutes: int = 2000, full_score: float = 100) -> pd.Series:
    """出场可靠性分：基于累计分钟数。线性插值，上限 100。"""
    minutes = pd.to_numeric(minutes, errors="coerce").fillna(0)
    raw = min_score + (minutes - min_minutes) / (full_minutes - min_minutes) * (full_score - min_score)
    return raw.clip(0, 100)


# ---------------------------------------------------------------------------
# 同位置核心表现评分
# ---------------------------------------------------------------------------


def score_core_performance(df: pd.DataFrame, weights_cfg: dict) -> pd.Series:
    """按位置分组，对各位置重点指标计算组内百分位，加权求和。

    Args:
        df: 含 standard_position 和各项 per90 列的 DataFrame。
        weights_cfg: scoring_weights.yaml 中 position_metrics 部分。

    Returns:
        每个球员的 0-100 同位置核心表现分。
    """
    reverse_metrics = set(weights_cfg.get("reverse_metrics", []))
    scores = pd.Series([50.0] * len(df), index=df.index)

    for pos, metrics in weights_cfg.get("position_metrics", {}).items():
        if pos not in _STANDARD_GROUPS:
            continue
        mask = df["standard_position"] == pos
        if mask.sum() == 0:
            continue
        group = df.loc[mask]
        pos_scores = pd.Series([0.0] * len(group), index=group.index)
        total_weight = 0.0

        for metric, weight in metrics.items():
            total_weight += weight

            if metric == "pass_completion":
                if "Total_Cmp%" in group.columns:
                    raw = pd.to_numeric(group["Total_Cmp%"], errors="coerce").fillna(50)
                    pct = _percentile_rank(raw)
                else:
                    pct = pd.Series([50.0] * len(group), index=group.index)
            elif metric == "def_actions_per90":
                pct = _safe_pct(group, "def_actions_per90")
            elif metric == "touches_att_pen_per90":
                # 禁区触球 per90 = Touches_Att Pen / minutes * 90
                if "Touches_Att Pen" in group.columns:
                    minutes = pd.to_numeric(group["minutes"], errors="coerce").fillna(0)
                    safe = minutes.replace(0, np.nan)
                    raw = pd.to_numeric(group["Touches_Att Pen"], errors="coerce").fillna(0) / safe * 90
                    pct = _percentile_rank(raw.fillna(0))
                else:
                    pct = pd.Series([50.0] * len(group), index=group.index)
            elif metric == "blocks_per90":
                if "Blocks_Blocks" in group.columns:
                    minutes = pd.to_numeric(group["minutes"], errors="coerce").fillna(0)
                    safe = minutes.replace(0, np.nan)
                    raw = pd.to_numeric(group["Blocks_Blocks"], errors="coerce").fillna(0) / safe * 90
                    pct = _percentile_rank(raw.fillna(0))
                else:
                    pct = pd.Series([50.0] * len(group), index=group.index)
            else:
                pct = _safe_pct(group, metric)

            # 反向指标：百分位取反
            if metric in reverse_metrics:
                pct = 100 - pct

            pos_scores += pct * weight

        # 归一化
        if total_weight > 0:
            pos_scores /= total_weight
        scores.loc[mask] = pos_scores

    return scores


# ---------------------------------------------------------------------------
# 场上行为风格评分
# ---------------------------------------------------------------------------


def _avg_percentile(group: pd.DataFrame, cols: list[str]) -> pd.Series:
    """对 group 内多个列分别算百分位再取均值，缺失列贡献 50。"""
    if group.empty:
        return pd.Series(dtype=float)
    result = pd.Series([0.0] * len(group), index=group.index)
    valid = 0
    for col in cols:
        if col in group.columns:
            raw = pd.to_numeric(group[col], errors="coerce").fillna(0)
            result += _percentile_rank(raw)
            valid += 1
    if valid > 0:
        result /= valid
    else:
        result = 50.0
    return result


def score_behavior(df: pd.DataFrame, behavior_cfg: dict) -> pd.Series:
    """场上行为风格分：进攻主动性 / 推进 / 防守 / 纪律性四个维度加权。

    Args:
        df: 含各 per90 列的 DataFrame。
        behavior_cfg: scoring_weights.yaml 中 behavior 部分。

    Returns:
        0-100 行为风格分。
    """
    sub_w = behavior_cfg.get("sub_weights", {
        "attack": 0.30, "progression": 0.25, "defense": 0.25, "discipline": 0.20,
    })
    scores = pd.Series([50.0] * len(df), index=df.index)

    # Attack: goals + shots + dribbles + key_passes + shot_creating_actions per90
    attack_cols = ["goals_per90", "shots_per90", "dribbles_per90",
                   "key_passes_per90", "shot_creating_actions_per90"]
    scores += _avg_percentile(df, attack_cols) * sub_w.get("attack", 0.30)

    # Progression: progressive_carries_per90 + passes_per90
    prog_cols = ["progressive_carries_per90", "passes_per90"]
    scores += _avg_percentile(df, prog_cols) * sub_w.get("progression", 0.25)

    # Defense: tackles_per90 + interceptions_per90 + def_actions_per90
    def_cols = ["tackles_per90", "interceptions_per90", "def_actions_per90"]
    scores += _avg_percentile(df, def_cols) * sub_w.get("defense", 0.25)

    # Discipline: inverse of yellow + red per90
    discipline = pd.Series([50.0] * len(df), index=df.index)
    if "yellow_cards_per90" in df.columns:
        yp = pd.to_numeric(df["yellow_cards_per90"], errors="coerce").fillna(0)
        yp_pct = 100 - _percentile_rank(yp)  # lower is better
        discipline = yp_pct
    if "red_cards_per90" in df.columns:
        rp = pd.to_numeric(df["red_cards_per90"], errors="coerce").fillna(0)
        rp_pct = 100 - _percentile_rank(rp)
        discipline = (discipline + rp_pct) / 2
    scores += discipline * sub_w.get("discipline", 0.20)

    return scores.clip(0, 100)


# ---------------------------------------------------------------------------
# 风险扣分
# ---------------------------------------------------------------------------


def score_risk_penalty(df: pd.DataFrame, risk_cfg: dict) -> pd.Series:
    """计算风险扣分（0 到 -10）。

    扣分项：数据完整度低 / 黄牌过多 / 有红牌 / 分钟数不足。
    """
    max_penalty = risk_cfg.get("max_penalty", 10)
    rules = risk_cfg.get("rules", {})
    penalty = pd.Series([0.0] * len(df), index=df.index)

    # 数据完整度低
    if "data_completeness" in df.columns:
        comp = pd.to_numeric(df["data_completeness"], errors="coerce").fillna(1.0)
        threshold = rules.get("low_completeness_threshold", 0.7)
        penalty -= (comp < threshold).astype(float) * rules.get("low_completeness_penalty", 2)

    # 黄牌过多（反向：per90 高 = 不纪律）
    if "yellow_cards_per90" in df.columns:
        yp = pd.to_numeric(df["yellow_cards_per90"], errors="coerce").fillna(0)
        high_y = rules.get("high_yellow_per90", 1.5)
        penalty -= (yp > high_y).astype(float) * rules.get("high_yellow_penalty", 2)

    # 有红牌
    if "red_cards" in df.columns:
        rc = pd.to_numeric(df["red_cards"], errors="coerce").fillna(0)
        penalty -= (rc > 0).astype(float) * rules.get("any_red_card_penalty", 3)

    # 分钟数不足
    if "minutes" in df.columns:
        mins = pd.to_numeric(df["minutes"], errors="coerce").fillna(0)
        low_m = rules.get("low_minutes_threshold", 900)
        penalty -= (mins < low_m).astype(float) * rules.get("low_minutes_penalty", 3)

    return penalty.clip(-max_penalty, 0)


# ---------------------------------------------------------------------------
# 汇总评分
# ---------------------------------------------------------------------------


def score_players(
    df: pd.DataFrame,
    weights_cfg: dict,
    league_strength_map: dict[str, float] | None = None,
) -> pd.DataFrame:
    """执行完整潜力评分流程，返回含总分和分项得分的 DataFrame。

    公式：
      total_score = age_score × 0.15 + reliability_score × 0.15
                  + core_performance × 0.45 + behavior_score × 0.15
                  + league_score × 0.10 - risk_penalty

    Args:
        df: 阶段 3 输出的含 per90 特征的 DataFrame。
        weights_cfg: scoring_weights.yaml 解析结果。
        league_strength_map: {联赛名: 0-100 强度分}，None 则使用中性值 50。

    Returns:
        新增 total_score / age_score / reliability_score / core_performance /
        behavior_score / league_score / risk_penalty 列的**新** DataFrame。
    """
    out = df.copy()
    w = weights_cfg.get("weights", {})

    # 1. 年龄优势
    age_cfg = weights_cfg.get("age_scoring", {})
    out["age_score"] = score_age(
        out["age"],
        min_age=age_cfg.get("min_age", 15),
        max_age=age_cfg.get("max_age", 21),
        age_15_score=age_cfg.get("age_15_score", 100),
        age_21_score=age_cfg.get("age_21_score", 60),
    )

    # 2. 出场可靠性
    rel_cfg = weights_cfg.get("reliability", {})
    out["reliability_score"] = score_reliability(
        out["minutes"],
        min_minutes=rel_cfg.get("min_minutes", 600),
        min_score=rel_cfg.get("min_score", 50),
        full_minutes=rel_cfg.get("full_minutes", 2000),
        full_score=rel_cfg.get("full_score", 100),
    )

    # 3. 同位置核心表现
    out["core_performance"] = score_core_performance(out, weights_cfg)

    # 4. 场上行为风格
    out["behavior_score"] = score_behavior(out, weights_cfg.get("behavior", {}))

    # 5. 联赛强度（Opta Power Rankings）
    if league_strength_map is not None and "league" in out.columns:
        out["league_score"] = out["league"].map(league_strength_map).fillna(50.0)
    else:
        out["league_score"] = 50.0

    # 6. 风险扣分
    out["risk_penalty"] = score_risk_penalty(out, weights_cfg.get("risk_penalty", {}))

    # 汇总
    aw = w.get("age_score", 0.15)
    rw = w.get("reliability_score", 0.15)
    cw = w.get("core_performance", 0.45)
    bw = w.get("behavior_score", 0.15)
    lw = w.get("league_strength", 0.10)

    out["total_score"] = (
        out["age_score"] * aw
        + out["reliability_score"] * rw
        + out["core_performance"] * cw
        + out["behavior_score"] * bw
        + out["league_score"] * lw
        + out["risk_penalty"]
    ).clip(0, 100)

    return out
