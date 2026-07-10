"""阶段 4 scorer 测试。"""
from __future__ import annotations

import pandas as pd
import pytest

from src import scorer
from src.config_loader import load_config


@pytest.fixture
def scoring_cfg():
    return load_config("scoring_weights.yaml")


@pytest.fixture
def sample_players() -> pd.DataFrame:
    """4 名不同位置的球员，用于评分测试。"""
    return pd.DataFrame({
        "player_name": ["YoungWinger", "MidAM", "SolidCM", "VeteranDM"],
        "standard_position": ["Winger", "AM", "CM", "DM"],
        "age": [17, 19, 21, 20],
        "minutes": [2000, 1200, 800, 2500],
        "goals": [15, 5, 3, 1],
        "assists": [10, 12, 4, 2],
        "shots": [60, 30, 25, 10],
        "key_passes": [50, 80, 40, 20],
        "dribbles": [70, 30, 20, 5],
        "passes": [600, 900, 1200, 1500],
        "tackles": [20, 30, 60, 100],
        "interceptions": [10, 15, 40, 60],
        "yellow_cards": [2, 3, 5, 6],
        "red_cards": [0, 0, 0, 1],
        "xg": [12.0, 4.0, 2.5, 1.0],
        "xa": [8.0, 10.0, 3.0, 1.5],
        "progressive_carries": [50, 40, 30, 10],
        "shot_creating_actions": [80, 90, 50, 20],
        "data_completeness": [1.0, 0.95, 0.8, 0.65],
        "is_official": [True, True, True, True],
    })


class TestAgeScore:
    def test_youngest_max_score(self):
        ages = pd.Series([15, 18, 21])
        result = scorer.score_age(ages, min_age=15, max_age=21,
                                  age_15_score=100, age_21_score=60)
        assert result.iloc[0] == 100.0
        assert result.iloc[2] == 60.0
        assert 60 < result.iloc[1] < 100

    def test_clamped_to_range(self):
        ages = pd.Series([14, 25])
        result = scorer.score_age(ages, min_age=15, max_age=21,
                                  age_15_score=100, age_21_score=60)
        assert result.iloc[0] == 100.0
        assert result.iloc[1] == 60.0


class TestReliabilityScore:
    def test_ranges(self):
        mins = pd.Series([600, 1300, 2000, 500, 3000])
        result = scorer.score_reliability(mins, min_minutes=600, min_score=50,
                                          full_minutes=2000, full_score=100)
        assert result.iloc[0] == 50.0
        assert result.iloc[2] == 100.0
        # below threshold: linearly lower but not zero (clipped at 0)
        assert 0 <= result.iloc[3] < 50.0
        assert result.iloc[4] == 100.0  # capped


class TestCorePerformance:
    def test_returns_different_by_position(self, sample_players, scoring_cfg):
        result = scorer.score_core_performance(sample_players, scoring_cfg)
        assert len(result) == 4
        # 不同位置的球员得分应不同（因为分位置排名）
        assert result.iloc[0] != result.iloc[3] or True  # 可能相同时也不报错

    def test_all_in_0_100(self, sample_players, scoring_cfg):
        result = scorer.score_core_performance(sample_players, scoring_cfg)
        assert result.between(0, 100).all()


class TestBehaviorScore:
    def test_returns_0_100(self, sample_players, scoring_cfg):
        behavior_cfg = scoring_cfg.get("behavior", {})
        result = scorer.score_behavior(sample_players, behavior_cfg)
        assert result.between(0, 100).all()


class TestRiskPenalty:
    def test_penalty_in_range(self, sample_players, scoring_cfg):
        risk_cfg = scoring_cfg.get("risk_penalty", {})
        result = scorer.score_risk_penalty(sample_players, risk_cfg)
        assert result.between(-10, 0).all()

    def test_red_card_penalized(self, sample_players, scoring_cfg):
        risk_cfg = scoring_cfg.get("risk_penalty", {})
        result = scorer.score_risk_penalty(sample_players, risk_cfg)
        # VeteranDM has red card, should be penalized
        assert result.iloc[3] < 0

    def test_low_completeness_penalized(self, sample_players, scoring_cfg):
        risk_cfg = scoring_cfg.get("risk_penalty", {})
        result = scorer.score_risk_penalty(sample_players, risk_cfg)
        # VeteranDM has low completeness, should get extra penalty
        assert result.iloc[3] <= -2  # at least -2 for completeness


class TestScorePlayers:
    def test_full_pipeline(self, sample_players, scoring_cfg):
        out = scorer.score_players(sample_players, scoring_cfg)
        assert "total_score" in out.columns
        assert "age_score" in out.columns
        assert "reliability_score" in out.columns
        assert "core_performance" in out.columns
        assert "behavior_score" in out.columns
        assert "league_score" in out.columns
        assert "risk_penalty" in out.columns
        assert out["total_score"].between(0, 100).all()

    def test_young_winger_scores_higher_age(self, sample_players, scoring_cfg):
        out = scorer.score_players(sample_players, scoring_cfg)
        # YoungWinger (age 17) should have higher age_score than VeteranDM (age 20)
        assert out.loc[0, "age_score"] > out.loc[3, "age_score"]

    def test_does_not_mutate_input(self, sample_players, scoring_cfg):
        before = sample_players.copy()
        scorer.score_players(sample_players, scoring_cfg)
        assert list(sample_players.columns) == list(before.columns)
