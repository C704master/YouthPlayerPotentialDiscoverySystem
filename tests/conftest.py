"""共享测试夹具：合成的 FBref / Transfermarkt 样本数据。

这些夹具模拟 ScraperFC 的返回结构（含两级表头、粗位置、别名列名等），
使阶段 0-2 的处理逻辑可以完全离线、可复现地测试。
"""
from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def fbref_multiindex_df() -> pd.DataFrame:
    """模拟 FBref standard 分类返回的两级表头 player_stats。"""
    cols = pd.MultiIndex.from_tuples([
        ("Unnamed: 0_level_0", "Player"),
        ("Unnamed: 1_level_0", "player_id"),
        ("Unnamed: 2_level_0", "Squad"),
        ("Unnamed: 3_level_0", "Comp"),
        ("Unnamed: 4_level_0", "Age"),
        ("Unnamed: 5_level_0", "Pos"),
        ("Playing Time", "Min"),
        ("Performance", "Gls"),
        ("Performance", "Ast"),
        ("Per 90 Minutes", "Gls"),
    ])
    data = [
        [" Younes Winger", "p1", "Ajax", "Eredivisie", 20, "FW", 1800, 10, 5, 0.5],
        ["Midfield Maestro", "p2", "Barca", "La Liga", 19, "MF", 1200, 2, 8, 0.15],
    ]
    return pd.DataFrame(data, columns=cols)


@pytest.fixture
def fbref_players_df() -> pd.DataFrame:
    """模拟已扁平化、含内部标准字段名的 FBref 球员数据（阶段 1 输入前形态）。

    覆盖多种情况：U21 边锋、U21 中场、超龄球员、分钟不足球员、后卫、缺失年龄靠 DOB。
    """
    return pd.DataFrame({
        "player_name": [
            " Younes Winger", "Ana Attack", "Carl Central", "Dan Defense",
            "Old Timer", "Rookie Sub", "Dob Only",
        ],
        "player_id": ["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
        "team": ["Ajax", "Barca", "Roma", "Roma", "PSG", "Ajax", "Porto"],
        "league": ["EPL", "La Liga", "Serie A", "Serie A", "Ligue 1", "EPL", "Primeira Liga"],
        "age": [20, 19, 21, 20, 25, 18, None],
        "date_of_birth": [None, None, None, None, None, None, "2006-01-01"],
        "position": ["FW", "MF", "MF", "DF", "MF", "FW", "MF"],
        "minutes": [1800, 1200, 900, 1500, 2000, 200, 1000],
        "goals": [10, 2, 3, 0, 8, 1, 1],
        "assists": [5, 8, 4, 1, 3, 0, 2],
        "key_passes": [40, 60, 30, 5, 25, 3, 20],
        "tackles": [10, 12, 40, 60, 8, 1, 15],
        "interceptions": [8, 6, 30, 45, 5, 1, 10],
        "yellow_cards": [2, 3, 5, 7, 1, 0, 2],
        "red_cards": [0, 0, 1, 0, 0, 0, 0],
    })


@pytest.fixture
def transfermarkt_df() -> pd.DataFrame:
    """模拟 Transfermarkt 球员主位置数据（含译名/重音差异用于匹配测试）。"""
    return pd.DataFrame({
        "player_name": [
            "Younes Winger", "Ana Attack", "Carl Central", "Dan Defense",
            "Old Timer", "Rookie Sub", "Dob Only",
        ],
        "team": ["Ajax", "Barca", "Roma", "Roma", "PSG", "Ajax", "Porto"],
        "position": [
            "Right Winger", "Attacking Midfield", "Central Midfield",
            "Centre-Back", "Defensive Midfield", "Left Winger", "Central Midfield",
        ],
    })


@pytest.fixture
def field_mapping() -> dict:
    """最小字段映射（含大小写/别名差异）。"""
    return {
        "player_name": ["player_name", "name", "Player"],
        "minutes": ["minutes", "Min"],
        "goals": ["goals", "Gls"],
        "assists": ["assists", "Ast"],
        "position": ["position", "Pos"],
        "team": ["team", "Squad"],
        "league": ["league", "Comp"],
        "age": ["age", "Age"],
    }


@pytest.fixture
def position_mapping() -> dict:
    """位置映射（对应 config/position_mapping.yaml）。"""
    return {
        "Right Winger": "Winger",
        "Left Winger": "Winger",
        "Winger": "Winger",
        "Attacking Midfield": "AM",
        "Central Midfield": "CM",
        "Defensive Midfield": "DM",
    }


@pytest.fixture
def league_mapping() -> dict:
    """联赛名归一化映射。"""
    return {
        "EPL": "Premier League",
        "La Liga": "La Liga",
        "Serie A": "Serie A",
    }
