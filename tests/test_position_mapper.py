"""阶段 2 position_mapper 测试。"""
from __future__ import annotations

import pandas as pd

from src import position_mapper as pm


class TestMapTransfermarktPosition:
    def test_maps_known(self, position_mapping):
        assert pm.map_transfermarkt_position("Right Winger", position_mapping) == "Winger"
        assert pm.map_transfermarkt_position("Defensive Midfield", position_mapping) == "DM"

    def test_case_insensitive(self, position_mapping):
        assert pm.map_transfermarkt_position("central midfield", position_mapping) == "CM"

    def test_unknown_returns_none(self, position_mapping):
        assert pm.map_transfermarkt_position("Centre-Back", position_mapping) is None

    def test_nan_returns_none(self, position_mapping):
        assert pm.map_transfermarkt_position(float("nan"), position_mapping) is None
        assert pm.map_transfermarkt_position(None, position_mapping) is None


class TestHeuristicPosition:
    def test_fw_is_winger(self):
        assert pm.heuristic_position("FW") == "Winger"
        assert pm.heuristic_position("MF,FW") == "Winger"

    def test_mf_high_keypasses_is_am(self):
        assert pm.heuristic_position("MF", key_passes_per90=3.0, def_actions_per90=0.5) == "AM"

    def test_mf_high_defense_is_dm(self):
        assert pm.heuristic_position("MF", key_passes_per90=0.4, def_actions_per90=3.0) == "DM"

    def test_mf_balanced_is_cm(self):
        assert pm.heuristic_position("MF", key_passes_per90=1.0, def_actions_per90=1.0) == "CM"

    def test_defender_is_none(self):
        assert pm.heuristic_position("DF") is None
        assert pm.heuristic_position("GK") is None

    def test_nan_is_none(self):
        assert pm.heuristic_position(float("nan")) is None


class TestAssignStandardPosition:
    def test_prefers_transfermarkt(self, position_mapping):
        row = pd.Series({"tm_position": "Right Winger", "position": "MF"})
        pos, src = pm.assign_standard_position(row, position_mapping)
        assert pos == "Winger"
        assert src == pm.SRC_TM

    def test_falls_back_to_heuristic(self, position_mapping):
        row = pd.Series({"tm_position": None, "position": "FW"})
        pos, src = pm.assign_standard_position(row, position_mapping)
        assert pos == "Winger"
        assert src == pm.SRC_HEURISTIC

    def test_none_when_both_fail(self, position_mapping):
        row = pd.Series({"tm_position": "Centre-Back", "position": "DF"})
        pos, src = pm.assign_standard_position(row, position_mapping)
        assert pos is None
        assert src == pm.SRC_NONE


class TestAddStandardPosition:
    def test_adds_columns(self, fbref_players_df, transfermarkt_df, position_mapping):
        from src import collector
        merged = collector.attach_position(fbref_players_df, transfermarkt_df)
        out = pm.add_standard_position(merged, position_mapping)
        assert "standard_position" in out.columns
        assert "position_source" in out.columns
        winger = out[out["player_name"] == " Younes Winger"].iloc[0]
        assert winger["standard_position"] == "Winger"
        assert winger["position_source"] == pm.SRC_TM
