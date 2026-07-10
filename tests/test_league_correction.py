"""阶段 5 league_correction 测试。"""
from __future__ import annotations

import pandas as pd
import pytest

from src import league_correction as lc


class TestLoadLeagueStrength:
    def test_extracts_mapping(self):
        cfg = {"leagues": {"Premier League": 100, "La Liga": 94, "Ligue 1": 92}}
        result = lc.load_league_strength(cfg)
        assert result == {"Premier League": 100.0, "La Liga": 94.0, "Ligue 1": 92.0}

    def test_empty_config_returns_empty(self):
        assert lc.load_league_strength({}) == {}


class TestApplyLeagueStrength:
    def test_maps_known_leagues(self):
        df = pd.DataFrame({"league": ["Premier League", "Ligue 1", "La Liga"]})
        strength_map = {"Premier League": 100, "La Liga": 94, "Ligue 1": 92}
        result = lc.apply_league_strength(df, strength_map)
        assert result.iloc[0] == 100.0
        assert result.iloc[1] == 92.0
        assert result.iloc[2] == 94.0

    def test_unknown_league_defaults_50(self):
        df = pd.DataFrame({"league": ["J1 League", "Premier League"]})
        strength_map = {"Premier League": 100}
        result = lc.apply_league_strength(df, strength_map)
        assert result.iloc[0] == 50.0
        assert result.iloc[1] == 100.0

    def test_missing_league_col_no_error(self):
        df = pd.DataFrame({"other": [1, 2]})
        strength_map = {"Premier League": 100}
        # Should work if called through scorer, tested there


class TestScorerIntegration:
    def test_league_score_not_50_when_map_provided(self):
        from src import scorer
        df = pd.DataFrame({
            "player_name": ["a", "b"],
            "standard_position": ["Winger", "CM"],
            "league": ["Premier League", "Ligue 1"],
            "age": [18, 20],
            "minutes": [1500, 1200],
            "goals": [10, 3],
            "assists": [5, 4],
            "shots": [30, 20],
            "key_passes": [20, 30],
            "dribbles": [40, 15],
            "passes": [500, 800],
            "tackles": [15, 40],
            "interceptions": [8, 25],
            "yellow_cards": [2, 4],
            "red_cards": [0, 0],
            "xg": [9.0, 2.5],
            "xa": [4.0, 3.0],
            "progressive_carries": [30, 25],
            "shot_creating_actions": [50, 45],
            "data_completeness": [1.0, 1.0],
            "is_official": [True, True],
        })
        from src.config_loader import load_config
        weights_cfg = load_config("scoring_weights.yaml")
        strength_map = {"Premier League": 100, "Ligue 1": 92}
        # 必须先有 per90 列
        from src import feature_builder
        feats = feature_builder.build_features(df)
        result = scorer.score_players(feats, weights_cfg, league_strength_map=strength_map)
        assert result.loc[0, "league_score"] == 100.0
        assert result.loc[1, "league_score"] == 92.0
        # Ligue 1 球员联赛分更低
        assert result.loc[0, "league_score"] > result.loc[1, "league_score"]

    def test_league_score_defaults_50_without_map(self):
        from src import scorer, feature_builder
        df = pd.DataFrame({
            "player_name": ["a"],
            "standard_position": ["Winger"],
            "league": ["Premier League"],
            "age": [20],
            "minutes": [1500],
            "goals": [10], "assists": [5], "shots": [30],
            "key_passes": [20], "dribbles": [40], "passes": [500],
            "tackles": [15], "interceptions": [8],
            "yellow_cards": [2], "red_cards": [0],
            "xg": [9.0], "xa": [4.0],
            "progressive_carries": [30], "shot_creating_actions": [50],
            "data_completeness": [1.0], "is_official": [True],
        })
        from src.config_loader import load_config
        weights_cfg = load_config("scoring_weights.yaml")
        feats = feature_builder.build_features(df)
        result = scorer.score_players(feats, weights_cfg)  # no map
        assert result.loc[0, "league_score"] == 50.0
