"""阶段 1 data_loader 测试。"""
from __future__ import annotations

import pandas as pd
import pytest

from src import data_loader as dl


class TestFieldMapping:
    def test_invert_includes_std_and_aliases(self, field_mapping):
        inv = dl.invert_field_mapping(field_mapping)
        assert inv["gls"] == "goals"
        assert inv["goals"] == "goals"
        assert inv["min"] == "minutes"

    def test_apply_renames_aliases(self, field_mapping):
        df = pd.DataFrame({"Player": ["x"], "Gls": [1], "Min": [900]})
        out = dl.apply_field_mapping(df, field_mapping)
        assert set(["player_name", "goals", "minutes"]).issubset(out.columns)

    def test_apply_case_insensitive(self, field_mapping):
        df = pd.DataFrame({"PLAYER": ["x"], "gLs": [1]})
        out = dl.apply_field_mapping(df, field_mapping)
        assert "player_name" in out.columns
        assert "goals" in out.columns

    def test_unknown_columns_kept(self, field_mapping):
        df = pd.DataFrame({"Gls": [1], "weird_col": [2]})
        out = dl.apply_field_mapping(df, field_mapping)
        assert "weird_col" in out.columns

    def test_duplicate_alias_keeps_first(self, field_mapping):
        # goals 和 Gls 同时存在，都会映射到 goals，只保留第一个
        df = pd.DataFrame({"goals": [1], "Gls": [2]})
        out = dl.apply_field_mapping(df, field_mapping)
        assert list(out.columns).count("goals") == 1


class TestCheckFields:
    def test_full_report_can_analyze(self, fbref_players_df):
        report = dl.check_fields(fbref_players_df)
        assert report.n_rows == len(fbref_players_df)
        assert report.missing_required == []
        assert report.has_age is True
        assert report.can_analyze is True

    def test_missing_required_blocks_analysis(self):
        df = pd.DataFrame({"player_name": ["x"], "age": [20]})
        report = dl.check_fields(df)
        assert "minutes" in report.missing_required
        assert report.can_analyze is False

    def test_age_via_dob_only(self):
        df = pd.DataFrame({
            "player_name": ["x"], "position": ["FW"], "team": ["t"],
            "league": ["EPL"], "minutes": [900], "date_of_birth": ["2005-01-01"],
        })
        report = dl.check_fields(df)
        assert report.has_age is True
        assert report.can_analyze is True

    def test_missing_age_entirely(self):
        df = pd.DataFrame({
            "player_name": ["x"], "position": ["FW"], "team": ["t"],
            "league": ["EPL"], "minutes": [900],
        })
        report = dl.check_fields(df)
        assert report.has_age is False
        assert report.can_analyze is False

    def test_core_and_enhance_missing_tracked(self, fbref_players_df):
        report = dl.check_fields(fbref_players_df)
        # 夹具没有 shots/xg 等
        assert "shots" in report.missing_core
        assert "xg" in report.missing_enhance


class TestFormatReport:
    def test_contains_row_count_and_warning(self):
        df = pd.DataFrame({"player_name": ["x"]})
        report = dl.check_fields(df)
        text = dl.format_report(report)
        assert "读取行数: 1" in text
        assert "警告" in text

    def test_ok_report_no_warning(self, fbref_players_df):
        report = dl.check_fields(fbref_players_df)
        text = dl.format_report(report)
        assert "可正式分析: 是" in text
        assert "警告" not in text


class TestLoadPlayers:
    def test_reads_maps_and_reports(self, tmp_path, field_mapping):
        raw = pd.DataFrame({"Player": ["x"], "Gls": [1], "Age": [20],
                            "Pos": ["FW"], "Squad": ["t"], "Comp": ["EPL"],
                            "Min": [900]})
        csv = tmp_path / "players.csv"
        raw.to_csv(csv, index=False)
        df, report = dl.load_players(csv, field_mapping)
        assert "player_name" in df.columns
        assert report.n_rows == 1

    def test_missing_file_raises(self, field_mapping):
        with pytest.raises(FileNotFoundError):
            dl.load_players("does_not_exist.csv", field_mapping)
