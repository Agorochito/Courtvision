
"""Read locally exported NBA data for CourtVision.

This module replaces live NBA API requests with
verified player-season snapshots.
"""

import json
import unicodedata
from functools import lru_cache
from pathlib import Path


SNAPSHOT_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "nba_snapshot.json"
)


@lru_cache(maxsize=1)
def load_snapshot():
    """Load the exported NBA JSON file once."""

    if not SNAPSHOT_PATH.exists():
        raise FileNotFoundError(
            "NBA snapshot not found. "
            "Run python export_nba_data.py first."
        )

    with SNAPSHOT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def normalize_name(name):
    """Match names regardless of case or accents."""

    name = unicodedata.normalize(
        "NFKD",
        name.strip(),
    )

    name = "".join(
        character
        for character in name
        if not unicodedata.combining(character)
    )

    return " ".join(name.casefold().split())


def find_player(name):
    """Find a player included in the snapshot."""

    if not name.strip():
        return None

    target = normalize_name(name)

    for player in load_snapshot()["players"].values():
        if normalize_name(player["full_name"]) == target:
            return {
                "id": player["id"],
                "full_name": player["full_name"],
            }

    return None


def get_player_record(player_id):
    """Get a saved player's complete snapshot record."""

    record = load_snapshot()["players"].get(
        str(player_id)
    )

    if record is None:
        raise ValueError(
            "This player is not in the current "
            "CourtVision demo dataset."
        )

    return record


def career_rows(player_id):
    """Return season rows for supported seasons only."""

    record = get_player_record(player_id)

    supported_seasons = set(
        record["seasons"].keys()
    )

    return [
        row
        for row in record["career_rows"]
        if row["SEASON_ID"] in supported_seasons
    ]


def get_game_log(player_id, season):
    """Get saved game logs without calling the NBA API."""

    record = get_player_record(player_id)

    season_data = record["seasons"].get(season)

    if season_data is None:
        raise ValueError(
            f"Season {season} is not available "
            "in the current demo dataset."
        )

    return season_data["games"]


def get_shots(player_id, season):
    """Get saved shot data without calling the NBA API."""

    record = get_player_record(player_id)

    season_data = record["seasons"].get(season)

    if season_data is None:
        return []

    return season_data.get("shots", [])


def available_seasons(rows):
    """List only seasons supported by the snapshot."""

    return sorted(
        {
            row["SEASON_ID"]
            for row in rows
        },
        reverse=True,
    )
