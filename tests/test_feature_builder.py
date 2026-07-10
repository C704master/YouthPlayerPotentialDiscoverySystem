"""阶段 3 feature_builder 测试。"""
from __future__ import annotations

import pandas as pd

from src import feature_builder as fb


class TestBuildFeatures:
    def test_computes_per90_for_core_fields(self):
        df = pd.DataFrame({
            "minutes": [900, 1800],
            "goals": [10, 20],
            "assists": [5, 10],
            "tackles": [30, 60],
        })
        out = fb.build_features(df)
        assert out.loc[0, "goals_per90"] == 1.0
        assert out.loc[1, "goals_per90"] == 1.0
        assert out.loc[0, "assists_per90"] == 0.5
        assert out.loc[1, "assists_per90"] == 0.5
        assert out.loc[0, "tackles_per90"] == 3.0

    def test_zero_minutes_returns_zero(self):
        df = pd.DataFrame({"minutes": [0], "goals": [5], "assists": [3]})
        out = fb.build_features(df)
        assert out.loc[0, "goals_per90"] == 0.0
        assert out.loc[0, "assists_per90"] == 0.0

    def test_missing_field_no_error(self):
        df = pd.DataFrame({"minutes": [900], "goals": [5]})
        out = fb.build_features(df)
        # assists 不存在，不会创建 assists_per90
        assert "goals_per90" in out.columns

    def test_does_not_overwrite_existing_per90(self):
        df = pd.DataFrame({
            "minutes": [900], "key_passes": [20], "key_passes_per90": [99.0],
        })
        out = fb.build_features(df)
        # 已有 key_passes_per90 不应被覆盖
        assert out.loc[0, "key_passes_per90"] == 99.0

    def test_computes_def_actions_per90(self):
        df = pd.DataFrame({
            "minutes": [900], "tackles": [30], "interceptions": [15],
        })
        out = fb.build_features(df)
        assert out.loc[0, "def_actions_per90"] == (30 + 15) / 900 * 90

    def test_enhance_fields_computed(self):
        df = pd.DataFrame({
            "minutes": [900], "xg": [9.0], "xa": [4.5],
            "progressive_carries": [18], "shot_creating_actions": [36],
        })
        out = fb.build_features(df)
        assert out.loc[0, "xg_per90"] == 0.9
        assert out.loc[0, "xa_per90"] == 0.45
        assert out.loc[0, "progressive_carries_per90"] == 1.8
        assert out.loc[0, "shot_creating_actions_per90"] == 3.6

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"minutes": [900], "goals": [10]})
        before_cols = set(df.columns)
        fb.build_features(df)
        assert set(df.columns) == before_cols  # 输入未变
