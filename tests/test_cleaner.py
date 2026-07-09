"""阶段 2 cleaner 测试。"""
from __future__ import annotations

from datetime import date

import pandas as pd

from src import cleaner


class TestComputeAge:
    def test_basic(self):
        assert cleaner.compute_age_from_dob("2005-01-01", ref=date(2026, 1, 1)) == 21

    def test_birthday_not_reached(self):
        assert cleaner.compute_age_from_dob("2005-12-31", ref=date(2026, 6, 1)) == 20

    def test_invalid_returns_none(self):
        assert cleaner.compute_age_from_dob("not-a-date") is None
        assert cleaner.compute_age_from_dob(None) is None


class TestEnsureAge:
    def test_fills_from_dob(self):
        df = pd.DataFrame({"age": [None], "date_of_birth": ["2006-01-01"]})
        out = cleaner.ensure_age(df, ref=date(2026, 1, 1))
        assert out.loc[0, "age"] == 20

    def test_keeps_existing_age(self):
        df = pd.DataFrame({"age": [19], "date_of_birth": ["2000-01-01"]})
        out = cleaner.ensure_age(df, ref=date(2026, 1, 1))
        assert out.loc[0, "age"] == 19


class TestFilterAge:
    def test_removes_over_age_and_nan(self):
        df = pd.DataFrame({"age": [21, 22, None]})
        out = cleaner.filter_age(df, max_age=21)
        assert list(out["age"]) == [21]


class TestMarkEligibility:
    def test_marks_official_by_minutes(self):
        df = pd.DataFrame({"minutes": [600, 599, None]})
        out = cleaner.mark_eligibility(df, min_minutes=600)
        assert list(out["is_official"]) == [True, False, False]


class TestHandleMissing:
    def test_drops_missing_required(self):
        df = pd.DataFrame({
            "player_name": ["a", None], "position": ["FW", "MF"],
            "team": ["t", "u"], "league": ["EPL", "EPL"], "minutes": [900, 900],
        })
        out = cleaner.handle_missing(df)
        assert len(out) == 1

    def test_fills_count_fields_zero(self):
        df = pd.DataFrame({
            "player_name": ["a"], "position": ["FW"], "team": ["t"],
            "league": ["EPL"], "minutes": [900], "goals": [None],
        })
        out = cleaner.handle_missing(df)
        assert out.loc[0, "goals"] == 0


class TestDedupe:
    def test_by_player_id(self):
        df = pd.DataFrame({"player_id": ["p1", "p1", "p2"], "x": [1, 2, 3]})
        out = cleaner.dedupe(df)
        assert len(out) == 2

    def test_by_name_team_league_when_no_id(self):
        df = pd.DataFrame({
            "player_name": ["a", "a"], "team": ["t", "t"], "league": ["EPL", "EPL"],
        })
        out = cleaner.dedupe(df)
        assert len(out) == 1


class TestCompleteness:
    def test_ratio(self):
        df = pd.DataFrame({"goals": [1], "assists": [None], "tackles": [2]})
        out = cleaner.compute_data_completeness(df)
        assert 0 < out.loc[0, "data_completeness"] <= 1


class TestCleanIntegration:
    def test_full_pipeline_filters_correctly(
        self, fbref_players_df, transfermarkt_df, position_mapping
    ):
        from src import collector
        merged = collector.attach_position(fbref_players_df, transfermarkt_df)
        out = cleaner.clean(
            merged, position_mapping, max_age=21, min_minutes=600,
            ref=date(2026, 1, 1),
        )
        # 验收：无 age>21
        assert (out["age"] <= 21).all()
        # 验收：只含 Winger/AM/CM/DM
        assert set(out["standard_position"]).issubset({"Winger", "AM", "CM", "DM"})
        # 后卫 Dan Defense（Centre-Back）应被过滤掉
        assert "Dan Defense" not in set(out["player_name"])
        # 超龄 Old Timer（25）应被过滤
        assert "Old Timer" not in set(out["player_name"])

    def test_observation_list_kept_but_marked(
        self, fbref_players_df, transfermarkt_df, position_mapping
    ):
        from src import collector
        merged = collector.attach_position(fbref_players_df, transfermarkt_df)
        out = cleaner.clean(
            merged, position_mapping, max_age=21, min_minutes=600,
            ref=date(2026, 1, 1),
        )
        # Rookie Sub 200 分钟：仍保留（Winger），但 is_official=False
        rookie = out[out["player_name"] == "Rookie Sub"]
        assert len(rookie) == 1
        assert bool(rookie.iloc[0]["is_official"]) is False
