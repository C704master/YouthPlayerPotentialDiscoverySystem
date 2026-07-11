"""Build the static JSON payload used by the web interface."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "web" / "data" / "players.json"

FIELDS = [
    "league",
    "season",
    "team",
    "player_name",
    "nation_",
    "position",
    "standard_position",
    "tm_sub_position",
    "age",
    "minutes",
    "goals",
    "assists",
    "yellow_cards",
    "red_cards",
    "market_value",
    "fifa_overall",
    "fifa_potential",
    "is_official",
    "data_completeness",
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "dribbles_per90",
    "passes_per90",
    "tackles_per90",
    "interceptions_per90",
    "key_passes_per90",
    "def_actions_per90",
    "xg_per90",
    "xa_per90",
    "progressive_carries_per90",
    "shot_creating_actions_per90",
    "age_score",
    "reliability_score",
    "core_performance",
    "behavior_score",
    "league_score",
    "risk_penalty",
    "total_score",
]


def json_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def relative_asset(path: Path) -> str | None:
    if not path.exists():
        return None
    return "../" + path.relative_to(ROOT).as_posix()


def build_payload() -> dict:
    scored_path = ROOT / "data" / "processed" / "scored_players.csv"
    df = pd.read_csv(scored_path)
    ranked = df.sort_values("total_score", ascending=False).reset_index(drop=True)
    official = ranked[ranked["is_official"] == True].reset_index(drop=True)
    official_rank = {name: rank + 1 for rank, name in enumerate(official["player_name"])}

    players = []
    for overall_rank, (_, row) in enumerate(ranked.iterrows(), start=1):
        name = row["player_name"]
        item = {
            "id": str(overall_rank),
            "overall_rank": overall_rank,
            "official_rank": official_rank.get(name),
        }
        for field in FIELDS:
            item[field] = json_value(row.get(field))

        item["chart_path"] = relative_asset(ROOT / "outputs" / "charts" / f"{name}_radar.png")
        item["report_md_path"] = relative_asset(ROOT / "outputs" / "reports" / "reports_md" / f"{name}.md")
        item["report_docx_path"] = relative_asset(ROOT / "outputs" / "reports" / "reports_docx" / f"{name}.docx")
        players.append(item)

    return {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "data/processed/scored_players.csv",
        "players": players,
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(build_payload(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
