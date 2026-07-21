"""
Monte Carlo game model.
 
Given a matchup's expected margin and total (from feature engineering), simulates
many game outcomes to estimate:
  - home / away win probability
  - projected scores and margin distribution
  - spread cover probability (against an optional betting line)
  - over/under probability (against an optional total line)
  - a Wilson confidence interval on the home win probability
"""
 
import math
from typing import Any, Dict, Optional
 
import numpy as np
 
from config.settings import DEFAULT_N_SIMULATIONS, MARGIN_STD, TOTAL_STD
from engine.feature_engineering import compute_matchup
 
 
def _wilson_interval(p_hat: float, n: int, z: float = 1.96) -> tuple:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))
 
 
def simulate_game(
    home_id: str,
    away_id: str,
    rest_home: Optional[int] = None,
    rest_away: Optional[int] = None,
    neutral: bool = False,
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    seed: Optional[int] = None,
    spread: Optional[float] = None,
    total_line: Optional[float] = None,
) -> Dict[str, Any]:
    """Run a vectorised Monte Carlo simulation of a single game.
 
    `spread` is the home line (negative if home favoured, e.g. -6.5).
    `total_line` is the over/under points total.
    """
    matchup = compute_matchup(home_id, away_id, rest_home, rest_away, neutral)
    exp_margin = matchup["expected_margin"]
    exp_total = matchup["expected_total"]
 
    rng = np.random.default_rng(seed)
    margins = rng.normal(exp_margin, MARGIN_STD, n_simulations)
    totals = rng.normal(exp_total, TOTAL_STD, n_simulations)
 
    home_scores = (totals + margins) / 2.0
    away_scores = (totals - margins) / 2.0
 
    # Nudge exact ties (basketball has no ties) toward the pre-game favourite.
    ties = margins == 0
    margins = np.where(ties, np.sign(exp_margin) or 1.0, margins)
 
    home_wins = int(np.sum(margins > 0))
    home_win_prob = home_wins / n_simulations
 
    lo, hi = _wilson_interval(home_win_prob, n_simulations)
 
    result: Dict[str, Any] = {
        "home_id": matchup["home_id"],
        "away_id": matchup["away_id"],
        "n_simulations": n_simulations,
        "home_win_probability": round(home_win_prob, 4),
        "away_win_probability": round(1 - home_win_prob, 4),
        "home_win_ci": [round(lo, 4), round(hi, 4)],
        "projected_home_score": round(float(np.mean(home_scores)), 1),
        "projected_away_score": round(float(np.mean(away_scores)), 1),
        "expected_margin": round(float(np.mean(margins)), 2),
        "expected_total": round(float(np.mean(totals)), 1),
        "margin_std": round(float(np.std(margins)), 2),
        "margin_p10": round(float(np.percentile(margins, 10)), 1),
        "margin_p90": round(float(np.percentile(margins, 90)), 1),
        "elo_win_prob": matchup["elo_win_prob"],
        "features": matchup["features"],
    }
 
    if spread is not None:
        # Home covers when its margin beats the line: margin + spread > 0.
        cover = float(np.mean((margins + spread) > 0))
        result["spread"] = spread
        result["home_cover_probability"] = round(cover, 4)
        result["away_cover_probability"] = round(1 - cover, 4)
 
    if total_line is not None:
        over = float(np.mean(totals > total_line))
        result["total_line"] = total_line
        result["over_probability"] = round(over, 4)
        result["under_probability"] = round(1 - over, 4)
 
    return result
 
 
def simulate_series(
    team1: str,
    team2: str,
    best_of: int = 7,
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Simulate a best-of-N playoff series (team1 = higher seed, hosts 2-2-1-1-1)."""
    wins_needed = best_of // 2 + 1
    rng = np.random.default_rng(seed)
 
    # Per-game home win probabilities (team1 home vs team2 home).
    from engine.elo import get_elo_system
    elo = get_elo_system()
    p_t1_at_home = elo.expected_home_win_prob(team1, team2)
    p_t1_at_away = 1 - elo.expected_home_win_prob(team2, team1)
 
    # 2-2-1-1-1 host pattern for a 7-game series (team1 hosts games 1,2,5,7).
    host_pattern = [True, True, False, False, True, False, True][:best_of]
 
    t1_series_wins = 0
    for _ in range(n_simulations):
        w1 = w2 = 0
        for g in range(best_of):
            p = p_t1_at_home if host_pattern[g] else p_t1_at_away
            if rng.random() < p:
                w1 += 1
            else:
                w2 += 1
            if w1 == wins_needed or w2 == wins_needed:
                break
        if w1 > w2:
            t1_series_wins += 1
 
    p1 = t1_series_wins / n_simulations
    return {
        "team1": team1,
        "team2": team2,
        "best_of": best_of,
        "team1_series_win_probability": round(p1, 4),
        "team2_series_win_probability": round(1 - p1, 4),
    }