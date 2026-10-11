
"""CourtVision data access and basketball analytics."""

import sqlite3
import statistics
from pathlib import Path

from nba_api.stats.static import players
from nba_api.stats.endpoints import (
    playercareerstats,
    playergamelog,
    shotchartdetail,
)

DB_PATH = Path(__file__).with_name("courtvision.db")


def create_database():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                player_name TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS season_stats (
                player_id INTEGER,
                season TEXT,
                team TEXT,
                games INTEGER,
                ppg REAL,
                rpg REAL,
                apg REAL,
                spg REAL,
                fg_pct REAL,
                ts_pct REAL,
                PRIMARY KEY (player_id, season)
            )
        """)


def save_player(player_id, name):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT OR REPLACE INTO players VALUES (?, ?)",
            (player_id, name),
        )


def save_season_stats(player_id, stats):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """INSERT OR REPLACE INTO season_stats
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                player_id,
                stats["season"],
                stats["team"],
                stats["games"],
                stats["ppg"],
                stats["rpg"],
                stats["apg"],
                stats["spg"],
                stats["fg_pct"],
                stats["ts_pct"],
            ),
        )


def get_saved_players():
    with sqlite3.connect(DB_PATH) as db:
        return db.execute(
            "SELECT player_id, player_name FROM players ORDER BY player_name"
        ).fetchall()


def get_saved_season_stats():
    with sqlite3.connect(DB_PATH) as db:
        return db.execute("SELECT * FROM season_stats").fetchall()


def find_player(name):
    name = name.strip()

    if not name:
        return None

    matches = players.find_players_by_full_name(name)

    exact = next(
        (
            p for p in matches
            if p["full_name"].casefold() == name.casefold()
        ),
        None,
    )

    return (exact or matches[0]) if matches else None


def career_rows(player_id):
    data = playercareerstats.PlayerCareerStats(
        player_id=player_id,
        timeout=20,
    ).get_dict()

    result = data["resultSets"][0]

    return [
        dict(zip(result["headers"], row))
        for row in result["rowSet"]
    ]


def available_seasons(rows):
    return sorted(
        {row["SEASON_ID"] for row in rows},
        reverse=True,
    )


def calculate_stats(rows, season):
    matching = [
        row for row in rows
        if row["SEASON_ID"] == season
    ]

    if not matching:
        raise ValueError("No statistics for that season.")

    row = next(
        (
            item for item in matching
            if item["TEAM_ABBREVIATION"] == "TOT"
        ),
        matching[-1],
    )

    games = row["GP"]

    if not games:
        raise ValueError("No games played in this season.")

    attempts = row["FGA"] + 0.44 * row["FTA"]

    return {
        "season": season,
        "team": row["TEAM_ABBREVIATION"],
        "games": games,
        "ppg": round(row["PTS"] / games, 1),
        "rpg": round(row["REB"] / games, 1),
        "apg": round(row["AST"] / games, 1),
        "spg": round(row["STL"] / games, 1),
        "fg_pct": round(row["FG_PCT"] * 100, 1),
        "ts_pct": (
            round(row["PTS"] / (2 * attempts) * 100, 1)
            if attempts else 0
        ),
        "two_pts": max(
            0,
            (row["FGM"] - row["FG3M"]) * 2,
        ),
        "three_pts": row["FG3M"] * 3,
        "ft_pts": row["FTM"],
    }


def get_game_log(player_id, season):
    data = playergamelog.PlayerGameLog(
        player_id=player_id,
        season=season,
        timeout=20,
    ).get_dict()

    result = data["resultSets"][0]

    return [
        dict(zip(result["headers"], row))
        for row in result["rowSet"]
    ]


def calculate_recent_form(games):
    recent = games[:5]

    if not recent:
        return None

    return {
        key: round(
            sum(game[field] for game in recent) / len(recent),
            1,
        )
        for key, field in [
            ("ppg", "PTS"),
            ("rpg", "REB"),
            ("apg", "AST"),
        ]
    }


def calculate_scoring_consistency(games):
    if len(games) < 2:
        return None

    points = [game["PTS"] for game in games[:10]]

    return round(statistics.pstdev(points), 2)


def generate_performance_insight(stats, recent):
    if not recent:
        return "No game logs available for this season."

    difference = round(
        recent["ppg"] - stats["ppg"],
        1,
    )

    if difference == 0:
        return (
            f"Recent scoring matches the season "
            f"average of {stats['ppg']} PPG."
        )

    direction = (
        "above" if difference > 0 else "below"
    )

    return (
        f"Over the last five available games: "
        f"{recent['ppg']} PPG, "
        f"{abs(difference):.1f} points {direction} "
        f"the season average."
    )


def get_shots(player_id, season):
    """Fetch real shot coordinates from the NBA API."""

    data = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=player_id,
        season_nullable=season,
        season_type_all_star="Regular Season",
        context_measure_simple="FGA",
        timeout=20,
    ).get_dict()

    result = data["resultSets"][0]

    return [
        dict(zip(result["headers"], row))
        for row in result["rowSet"]
    ]
