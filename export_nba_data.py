
"""Export genuine NBA data for CourtVision's cloud deployment."""

import json
from datetime import datetime, timezone
from pathlib import Path

from main import (
    available_seasons,
    career_rows,
    find_player,
    get_game_log,
    get_shots,
)

# A practical starter dataset for our portfolio demo.
# We can add more players and seasons later.
PLAYERS_TO_EXPORT = [
    ("LeBron James", "2025-26"),
    ("Luka Doncic", "2025-26"),
    ("Shai Gilgeous-Alexander", "2025-26"),
    ("Anthony Edwards", "2025-26"),
    ("Stephen Curry", "2025-26"),
    ("Kobe Bryant", "2009-10"),
    ("Michael Jordan", "1995-96"),
]

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = DATA_DIR / "nba_snapshot.json"


def save_snapshot(snapshot):
    """Write the JSON safely after each successful export."""
    DATA_DIR.mkdir(exist_ok=True)

    temporary = OUTPUT_FILE.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(
            snapshot,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary.replace(OUTPUT_FILE)


def main():
    snapshot = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": "NBA statistics via nba_api",
        "players": {},
    }

    print("\nCOURTVISION NBA DATA EXPORT")
    print("=" * 45)

    for name, season in PLAYERS_TO_EXPORT:
        print(f"\nFetching {name} — {season}")

        try:
            player = find_player(name)

            if player is None:
                print("  SKIPPED: Player not found.")
                continue

            player_id = player["id"]

            career = career_rows(player_id)
            seasons = available_seasons(career)

            if season not in seasons:
                print("  SKIPPED: Season not available.")
                continue

            # Game logs are essential for scoring charts,
            # recent-form analysis, and consistency.
            games = get_game_log(player_id, season)

            if not games:
                print("  SKIPPED: No game logs returned.")
                continue

            # Shot locations are optional. We don't want
            # a shot-chart timeout to prevent the player
            # from being included in the snapshot.
            try:
                shots = get_shots(player_id, season)

                # Only save the fields our shot chart uses.
                shots = [
                    {
                        "LOC_X": shot["LOC_X"],
                        "LOC_Y": shot["LOC_Y"],
                        "SHOT_MADE_FLAG": shot["SHOT_MADE_FLAG"],
                    }
                    for shot in shots
                    if shot.get("LOC_X") is not None
                    and shot.get("LOC_Y") is not None
                ]

            except Exception as error:
                print(f"  Shot data unavailable: {error}")
                shots = []

            record = {
                "id": player_id,
                "full_name": player["full_name"],
                "career_rows": career,
                "seasons": {
                    season: {
                        "games": games,
                        "shots": shots,
                    }
                },
            }

            snapshot["players"][str(player_id)] = record
            save_snapshot(snapshot)

            print(f"  Saved {len(games)} game logs")
            print(f"  Saved {len(shots)} shots")
            print("  SUCCESS")

        except Exception as error:
            print(f"  FAILED: {error}")
            print("  Moving to the next player.")

    print("\n" + "=" * 45)
    print(
        f"Exported {len(snapshot['players'])} "
        "players successfully."
    )

    if snapshot["players"]:
        print(f"File saved: {OUTPUT_FILE}")
    else:
        print("No data could be exported.")


if __name__ == "__main__":
    main()
