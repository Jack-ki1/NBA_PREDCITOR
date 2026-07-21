"""
Feature engineering for NBA matchups.
 
Turns two team profiles plus schedule context (rest, neutral court) into the two
quantities the Monte Carlo model needs:
 
  - expected_margin  : expected final point differential (home - away)
  - expected_total   : expected combined score
 
The expected margin blends the pure Elo expectation with weighted feature
adjustments (net-rating gap, recent form, rest differential). Each contribution
is expressed in points so weights are interpretable.
"""
 
from typing import Any, Dict, Optional
 
from config.settings import (
    BACK_TO_BACK_PENALTY,
    FEATURE_WEIGHTS,
    LEAGUE_AVG_ORTG,
    LEAGUE_AVG_PACE,
    RECENCY_DECAY,
    RECENCY_WINDOW,
    REST_ADVANTAGE_PER_DAY,
)
from data.team_data import get_team
from engine.elo import get_elo_system
 
 
def compute_net_rating(team_id: str) -> float:
    """Season net rating (offensive minus defensive rating, per 100)."""
    team = get_team(team_id)
    return team.get("off_rating", LEAGUE_AVG_ORTG) - team.get("def_rating", LEAGUE_AVG_ORTG)
 
 
def compute_recent_form(team_id: str) -> float:
    """Exponentially-weighted average point differential over recent games.
 
    Falls back to the completed-game log when a static ``recent_form`` list is
    unavailable. Returns average margin (points); positive = winning form.
    """
    team = get_team(team_id)
    form = team.get("recent_form")
    if not form:
        from data.season_results import get_team_recent_results
        form = get_team_recent_results(team_id, RECENCY_WINDOW)
    if not form:
        return 0.0
 
    weighted_sum = 0.0
    weight_total = 0.0
    for i, diff in enumerate(form[:RECENCY_WINDOW]):
        w = RECENCY_DECAY ** i
        weighted_sum += w * diff
        weight_total += w
    return weighted_sum / weight_total if weight_total else 0.0
 
 
def compute_expected_pace(home_id: str, away_id: str) -> float:
    """Estimated possessions for the game from both teams' paces."""
    home = get_team(home_id)
    away = get_team(away_id)
    return (home.get("pace", LEAGUE_AVG_PACE) + away.get("pace", LEAGUE_AVG_PACE)) / 2.0
 
 
def _rest_adjustment(rest_home: Optional[int], rest_away: Optional[int]) -> float:
    """Points added to home margin from rest differential and back-to-backs."""
    adj = 0.0
    if rest_home is not None and rest_away is not None:
        adj += (rest_home - rest_away) * REST_ADVANTAGE_PER_DAY
    if rest_home == 1:
        adj -= BACK_TO_BACK_PENALTY
    if rest_away == 1:
        adj += BACK_TO_BACK_PENALTY
    return adj
 
 
def compute_matchup(
    home_id: str,
    away_id: str,
    rest_home: Optional[int] = None,
    rest_away: Optional[int] = None,
    neutral: bool = False,
) -> Dict[str, Any]:
    """Compute expected margin/total and the feature breakdown for a matchup."""
    home_id = home_id.upper()
    away_id = away_id.upper()
    elo = get_elo_system()
 
    # Baseline Elo expectation (already includes home-court advantage).
    elo_margin = elo.expected_margin(home_id, away_id, neutral=neutral)
    elo_win_prob = elo.expected_home_win_prob(home_id, away_id, neutral=neutral)
 
    net_diff = compute_net_rating(home_id) - compute_net_rating(away_id)
    form_diff = compute_recent_form(home_id) - compute_recent_form(away_id)
    rest_adj = _rest_adjustment(rest_home, rest_away)
 
    features = {
        "elo_diff": elo_margin,
        "net_rating_diff": net_diff,
        "recent_form": form_diff,
        "rest_advantage": rest_adj,
        # home_court is already folded into elo_margin; kept for transparency.
        "home_court": 0.0 if neutral else 0.0,
    }
 
    expected_margin = (
        FEATURE_WEIGHTS["elo_diff"] * features["elo_diff"]
        + FEATURE_WEIGHTS["net_rating_diff"] * features["net_rating_diff"]
        + FEATURE_WEIGHTS["recent_form"] * features["recent_form"]
        + FEATURE_WEIGHTS["rest_advantage"] * features["rest_advantage"]
    )
 
    pace = compute_expected_pace(home_id, away_id)
    home = get_team(home_id)
    away = get_team(away_id)
    # Points ≈ offensive rating vs opponent defence, blended, scaled by pace.
    home_pts = ((home.get("off_rating", LEAGUE_AVG_ORTG) + away.get("def_rating", LEAGUE_AVG_ORTG)) / 2) * pace / 100.0
    away_pts = ((away.get("off_rating", LEAGUE_AVG_ORTG) + home.get("def_rating", LEAGUE_AVG_ORTG)) / 2) * pace / 100.0
    expected_total = home_pts + away_pts
 
    return {
        "home_id": home_id,
        "away_id": away_id,
        "expected_margin": round(expected_margin, 3),
        "expected_total": round(expected_total, 2),
        "expected_pace": round(pace, 2),
        "elo_win_prob": round(elo_win_prob, 4),
        "features": {k: round(v, 3) for k, v in features.items()},
    }