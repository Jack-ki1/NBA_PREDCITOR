from engine.probability_model import simulate_game, simulate_series
 
 
def test_win_probabilities_sum_to_one():
    r = simulate_game("BOS", "LAL", n_simulations=5000, seed=1)
    assert abs(r["home_win_probability"] + r["away_win_probability"] - 1.0) < 1e-6
 
 
def test_stronger_home_team_favoured():
    r = simulate_game("OKC", "WAS", n_simulations=5000, seed=1)
    assert r["home_win_probability"] > 0.8
 
 
def test_seed_is_deterministic():
    a = simulate_game("BOS", "MIA", n_simulations=3000, seed=7)
    b = simulate_game("BOS", "MIA", n_simulations=3000, seed=7)
    assert a["home_win_probability"] == b["home_win_probability"]
 
 
def test_spread_and_total_probabilities():
    r = simulate_game("BOS", "LAL", n_simulations=5000, seed=1, spread=-6.5, total_line=228)
    assert 0.0 <= r["home_cover_probability"] <= 1.0
    assert abs(r["over_probability"] + r["under_probability"] - 1.0) < 1e-6
 
 
def test_series_probabilities_sum_to_one():
    r = simulate_series("OKC", "DAL", n_simulations=3000, seed=1)
    total = r["team1_series_win_probability"] + r["team2_series_win_probability"]
    assert abs(total - 1.0) < 1e-6
    assert r["team1_series_win_probability"] > 0.5  # OKC stronger