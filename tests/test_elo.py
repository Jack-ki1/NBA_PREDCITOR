from config.settings import ELO_HOME_ADVANTAGE
from engine.elo import TeamEloSystem, get_elo_system, reset_elo_system
 
 
def test_home_advantage_increases_win_prob():
    sys_ = TeamEloSystem()
    sys_.initialize_team("A", 1500)
    sys_.initialize_team("B", 1500)
    p_home = sys_.expected_home_win_prob("A", "B", neutral=False)
    p_neutral = sys_.expected_home_win_prob("A", "B", neutral=True)
    assert p_neutral == 0.5
    assert p_home > 0.5
 
 
def test_win_updates_ratings_zero_sum():
    sys_ = TeamEloSystem()
    sys_.initialize_team("A", 1500)
    sys_.initialize_team("B", 1500)
    before = sys_.get_rating("A") + sys_.get_rating("B")
    sys_.update_game("A", "B", 110, 100)
    after = sys_.get_rating("A") + sys_.get_rating("B")
    assert abs(before - after) < 1e-6  # zero-sum transfer
    assert sys_.get_rating("A") > 1500  # winner gains
    assert sys_.get_rating("B") < 1500  # loser loses
 
 
def test_blowout_moves_more_than_close_game():
    close = TeamEloSystem(); close.initialize_team("A"); close.initialize_team("B")
    blow = TeamEloSystem(); blow.initialize_team("A"); blow.initialize_team("B")
    close.update_game("A", "B", 101, 100)
    blow.update_game("A", "B", 130, 100)
    assert blow.get_rating("A") > close.get_rating("A")
 
 
def test_expected_margin_matches_home_advantage_at_equal_rating():
    sys_ = TeamEloSystem()
    sys_.initialize_team("A", 1500)
    sys_.initialize_team("B", 1500)
    margin = sys_.expected_margin("A", "B")
    assert margin > 0  # home team favoured by ~HCA/points_per_100
    assert abs(margin - ELO_HOME_ADVANTAGE / 28.0) < 0.5
 
 
def test_singleton_seeds_all_teams():
    reset_elo_system()
    elo = get_elo_system()
    assert len(elo.ratings) == 30
    reset_elo_system()