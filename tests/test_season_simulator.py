from config.settings import validate_settings
from engine.season_simulator import (
    _best_of_7_prob,
    simulate_playoffs,
    simulate_regular_season,
)
 
 
def test_settings_valid():
    v = validate_settings()
    assert v["valid"], v["errors"]
    assert v["team_count"] == 30
 
 
def test_best_of_7_monotonic():
    assert _best_of_7_prob(0.5) == 0.5
    assert _best_of_7_prob(0.6) > 0.6  # series amplifies edge
    assert _best_of_7_prob(0.4) < 0.4
 
 
def test_regular_season_probabilities_bounded():
    res = simulate_regular_season(n_simulations=200, seed=1)
    assert len(res["standings"]) == 30
    for row in res["standings"]:
        assert 0.0 <= row["playoff_probability"] <= 1.0
        assert row["projected_wins"] >= row["current_wins"]
 
 
def test_title_probabilities_sum_to_one():
    res = simulate_playoffs(n_simulations=300, seed=1)
    total = sum(t["title_probability"] for t in res["teams"])
    # Per-team probabilities are rounded to 4 dp, so allow small aggregate drift.
    assert abs(total - 1.0) < 2e-3