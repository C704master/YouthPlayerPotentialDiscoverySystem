"""阶段 0 collector 纯函数测试。"""
from __future__ import annotations

import pandas as pd
import pytest

from src import collector


class TestFlattenColumns:
    def test_flattens_multiindex_and_disambiguates(self, fbref_multiindex_df):
        out = collector.flatten_columns(fbref_multiindex_df)
        # 顶层 Unnamed → 只取底层
        assert "Player" in out.columns
        assert "player_id" in out.columns
        # 有意义顶层且底层重名 → 拼接以区分
        assert "Performance_Gls" in out.columns
        assert "Per 90 Minutes_Gls" in out.columns
        assert "Playing Time_Min" in out.columns

    def test_does_not_mutate_input(self, fbref_multiindex_df):
        before = fbref_multiindex_df.columns.tolist()
        collector.flatten_columns(fbref_multiindex_df)
        assert fbref_multiindex_df.columns.tolist() == before

    def test_plain_columns_passthrough(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        out = collector.flatten_columns(df)
        assert list(out.columns) == ["a", "b"]


class TestNormalizeLeagueName:
    def test_maps_known(self, league_mapping):
        assert collector.normalize_league_name("EPL", league_mapping) == "Premier League"

    def test_case_insensitive(self, league_mapping):
        assert collector.normalize_league_name("epl", league_mapping) == "Premier League"

    def test_unknown_passthrough(self, league_mapping):
        assert collector.normalize_league_name("J1 League", league_mapping) == "J1 League"

    def test_none(self, league_mapping):
        assert collector.normalize_league_name(None, league_mapping) is None


class TestMergeStatCategories:
    def test_merges_on_key_and_adds_new_cols(self):
        a = pd.DataFrame({"player_id": ["p1", "p2"], "goals": [1, 2]})
        b = pd.DataFrame({"player_id": ["p1", "p2"], "tackles": [3, 4]})
        out = collector.merge_stat_categories([a, b])
        assert set(out.columns) == {"player_id", "goals", "tackles"}
        assert len(out) == 2

    def test_outer_merge_keeps_all_players(self):
        a = pd.DataFrame({"player_id": ["p1"], "goals": [1]})
        b = pd.DataFrame({"player_id": ["p2"], "tackles": [4]})
        out = collector.merge_stat_categories([a, b])
        assert set(out["player_id"]) == {"p1", "p2"}

    def test_duplicate_columns_not_exploded(self):
        a = pd.DataFrame({"player_id": ["p1"], "goals": [1]})
        b = pd.DataFrame({"player_id": ["p1"], "goals": [1], "assists": [2]})
        out = collector.merge_stat_categories([a, b])
        # goals 只保留一份
        assert list(out.columns).count("goals") == 1
        assert "assists" in out.columns

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            collector.merge_stat_categories([])

    def test_missing_key_raises(self):
        with pytest.raises(ValueError):
            collector.merge_stat_categories([pd.DataFrame({"x": [1]})])


class TestNormName:
    def test_deburr_and_lowercase(self):
        assert collector.norm_name("Nicolò Zanióli") == "nicolo zanioli"

    def test_strips_punctuation_and_spaces(self):
        assert collector.norm_name("  A.  B-C ") == "a b c"

    def test_none_returns_empty(self):
        assert collector.norm_name(None) == ""


class TestAttachPosition:
    def test_attaches_matching_position(self, fbref_players_df, transfermarkt_df):
        out = collector.attach_position(fbref_players_df, transfermarkt_df)
        assert "tm_position" in out.columns
        row = out[out["player_name"] == " Younes Winger"].iloc[0]
        assert row["tm_position"] == "Right Winger"

    def test_unmatched_is_nan(self, fbref_players_df, transfermarkt_df):
        tm = transfermarkt_df[transfermarkt_df["player_name"] != "Ana Attack"]
        out = collector.attach_position(fbref_players_df, tm)
        row = out[out["player_name"] == "Ana Attack"].iloc[0]
        assert pd.isna(row["tm_position"])

    def test_row_count_preserved(self, fbref_players_df, transfermarkt_df):
        out = collector.attach_position(fbref_players_df, transfermarkt_df)
        assert len(out) == len(fbref_players_df)


class TestFinalizeRaw:
    def test_adds_normalized_league_and_season(self, league_mapping):
        df = pd.DataFrame({"player_id": ["p1"]})
        out = collector.finalize_raw(df, "EPL", "2024-2025", league_mapping)
        assert out.loc[0, "league"] == "Premier League"
        assert out.loc[0, "season"] == "2024-2025"
