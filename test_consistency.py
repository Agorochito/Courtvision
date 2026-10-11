
from backup_before_redesign.main import calculate_scoring_consistency

# Simulated NBA API response with the same structure
# our function expects.
def make_game_data(points):
    return {
        "resultSets": [
            {
                "headers": ["PTS"],
                "rowSet": [[point] for point in points]
            }
        ]
    }


# Test A: Exactly the same score in every game
player_a = make_game_data([20, 20, 20, 20, 20])

# Test B: Different scores, but the same average
player_b = make_game_data([10, 30, 15, 25, 20])

result_a = calculate_scoring_consistency(player_a)
result_b = calculate_scoring_consistency(player_b)

print("Player A standard deviation:", result_a)
print("Player B standard deviation:", result_b)

assert result_a == 0.0
assert result_b == 7.07

print("Both tests passed!")




from backup_before_redesign.main import calculate_recent_form

# Five games with known points, rebounds, and assists
recent_game_data = {
    "resultSets": [
        {
            "headers": ["PTS", "REB", "AST"],
            "rowSet": [
                [20, 5, 8],
                [30, 7, 6],
                [10, 3, 4],
                [25, 6, 7],
                [15, 4, 5]
            ]
        }
    ]
}

recent_stats = calculate_recent_form(recent_game_data)

print("Recent stats:", recent_stats)

assert recent_stats["ppg"] == 20.0
assert recent_stats["rpg"] == 5.0
assert recent_stats["apg"] == 6.0

print("Recent form tests passed!")




from backup_before_redesign.main import generate_performance_insight

season_stats = {"ppg": 25.0}

# Scenario 1: Recent scoring is above season average
above = generate_performance_insight(
    season_stats, {"ppg": 30.0}
)

# Scenario 2: Recent scoring is below season average
below = generate_performance_insight(
    season_stats, {"ppg": 20.0}
)

# Scenario 3: Recent scoring equals season average
equal = generate_performance_insight(
    season_stats, {"ppg": 25.0}
)

print("Above:", above)
print("Below:", below)
print("Equal:", equal)

assert "5.0" in above and "above" in above.lower()
assert "5.0" in below and "below" in below.lower()
assert "matches" in equal.lower()

print("Performance insight tests passed!")
