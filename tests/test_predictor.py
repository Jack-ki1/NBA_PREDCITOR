import pytest
 
from engine.predictor import GamePredictionRequest, clear_cache, predict_game
 
 
def test_predict_game_structure():
    clear_cache()
    res = predict_game(GamePredictionRequest("BOS", "LAL", n_simulations=2000, seed=1))
    assert res["meta"]["home_team"] == "Boston Celtics"
    assert res["meta"]["confidence"] in ("High", "Medium", "Low")
    assert 0.0 <= res["prediction"]["home_win_probability"] <= 1.0
 
 
def test_unknown_team_raises():
    clear_cache()
    with pytest.raises(KeyError):
        predict_game(GamePredictionRequest("ZZZ", "LAL", n_simulations=100, seed=1))
 
 
def test_cache_returns_same_object():
    clear_cache()
    req = GamePredictionRequest("BOS", "MIA", n_simulations=2000, seed=3)
    first = predict_game(req)
    second = predict_game(req)
    assert first is second