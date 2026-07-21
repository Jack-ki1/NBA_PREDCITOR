"""
Season & playoff Monte Carlo simulator.
 
Projects the rest of the regular season (win totals, playoff odds, seeding) and
runs a bracket simulation to estimate conference-finals, Finals, and title odds.
This is the NBA analogue of the F1 championship simulator.
"""
 
import math
from typing import Any, Dict, List, Optional
 
import numpy as np
 
from config.settings import CONFERENCES, DEFAULT_N_SIMULATIONS, PLAYOFF_TEAMS_PER_CONF
from data.schedule import generate_remaining_schedule
from data.season_results import get_team_record
from data.team_data import get_all_teams
from engine.elo import get_elo_system
 
 
def _best_of_7_prob(p_game: float) -> float:
    """Probability of winning a best-of-7 series given per-game win prob p."""
    p = min(max(p_game, 1e-6), 1 - 1e-6)
    total = 0.0
    for losses in range(4):  # opponent wins 0..3 games
        total += math.comb(3 + losses, losses) * (p ** 4) * ((1 - p) ** losses)
    return total
 
 
def _series_prob(higher_seed: str, lower_seed: str) -> float:
    """Higher seed's series win probability (small home-court seeding edge)."""
    elo = get_elo_system()
    # Neutral base plus a modest edge for holding home-court advantage.
    p_neutral = elo.expected_home_win_prob(higher_seed, lower_seed, neutral=True)
    p_game = min(0.95, p_neutral + 0.03)
    return _best_of_7_prob(p_game)
 
 
def simulate_regular_season(
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Vectorised remaining-season simulation → win totals and playoff odds."""
    teams = [t["id"] for t in get_all_teams()]
    idx = {t: i for i, t in enumerate(teams)}
    n_teams = len(teams)
 
    base_wins = np.array([get_team_record(t)["wins"] for t in teams], dtype=float)
 
    fixtures = generate_remaining_schedule()
    elo = get_elo_system()
    home_idx = np.array([idx[f["home"]] for f in fixtures])
    away_idx = np.array([idx[f["away"]] for f in fixtures])
    p_home = np.array([elo.expected_home_win_prob(f["home"], f["away"]) for f in fixtures])
 
    rng = np.random.default_rng(seed)
    n_fix = len(fixtures)
 
    total_wins = np.zeros((n_simulations, n_teams))
    playoff_counts = np.zeros(n_teams)
    top_seed_counts = np.zeros(n_teams)
 
    conf_of = {t["id"]: t["conference"] for t in get_all_teams()}
    east_mask = np.array([conf_of[t] == "East" for t in teams])
    west_mask = ~east_mask
 
    for s in range(n_simulations):
        draws = rng.random(n_fix) < p_home  # True => home wins
        wins = base_wins.copy()
        np.add.at(wins, home_idx, draws.astype(float))
        np.add.at(wins, away_idx, (~draws).astype(float))
        total_wins[s] = wins
 
        for mask in (east_mask, west_mask):
            conf_wins = np.where(mask, wins, -1)
            order = np.argsort(-conf_wins)
            playoff = order[:PLAYOFF_TEAMS_PER_CONF]
            playoff_counts[playoff] += 1
            top_seed_counts[order[0]] += 1
 
    avg_wins = total_wins.mean(axis=0)
    standings = []
    for t in teams:
        i = idx[t]
        standings.append({
            "team_id": t,
            "conference": conf_of[t],
            "current_wins": int(base_wins[i]),
            "projected_wins": round(float(avg_wins[i]), 1),
            "playoff_probability": round(float(playoff_counts[i] / n_simulations), 4),
            "top_seed_probability": round(float(top_seed_counts[i] / n_simulations), 4),
        })
    standings.sort(key=lambda x: x["projected_wins"], reverse=True)
    return {"n_simulations": n_simulations, "standings": standings}
 
 
def simulate_playoffs(
    n_simulations: int = DEFAULT_N_SIMULATIONS,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Simulate seeding + bracket → conference-finals, Finals, and title odds."""
    teams = [t["id"] for t in get_all_teams()]
    idx = {t: i for i, t in enumerate(teams)}
    conf_of = {t["id"]: t["conference"] for t in get_all_teams()}
 
    base_wins = np.array([get_team_record(t)["wins"] for t in teams], dtype=float)
    fixtures = generate_remaining_schedule()
    elo = get_elo_system()
    home_idx = np.array([idx[f["home"]] for f in fixtures])
    away_idx = np.array([idx[f["away"]] for f in fixtures])
    p_home = np.array([elo.expected_home_win_prob(f["home"], f["away"]) for f in fixtures])
    rng = np.random.default_rng(seed)
    n_fix = len(fixtures)
 
    conf_teams = {c: [t for t in teams if conf_of[t] == c] for c in CONFERENCES}
 
    title_counts = {t: 0 for t in teams}
    finals_counts = {t: 0 for t in teams}          # reached the NBA Finals
    conf_final_counts = {t: 0 for t in teams}      # reached the conference finals
 
    def run_bracket(seeded: List[str]):
        """Best-of-7 single-elim bracket over 8 seeds.
 
        Returns (conference_winner, [conference_finalists]).
        """
        round_teams = seeded
        conf_finalists: List[str] = []
        while len(round_teams) > 1:
            if len(round_teams) == 2:
                conf_finalists = list(round_teams)
            nxt = []
            n = len(round_teams)
            for i in range(n // 2):
                high, low = round_teams[i], round_teams[n - 1 - i]
                p = _series_prob(high, low)
                nxt.append(high if rng.random() < p else low)
            round_teams = nxt
        return round_teams[0], conf_finalists
 
    for _ in range(n_simulations):
        draws = rng.random(n_fix) < p_home
        wins = base_wins.copy()
        np.add.at(wins, home_idx, draws.astype(float))
        np.add.at(wins, away_idx, (~draws).astype(float))
 
        conf_winners = {}
        for c in CONFERENCES:
            ranked = sorted(conf_teams[c], key=lambda t: wins[idx[t]], reverse=True)
            seeded = ranked[:PLAYOFF_TEAMS_PER_CONF]
            winner, finalists = run_bracket(seeded)
            conf_winners[c] = winner
            finals_counts[winner] += 1
            for t in finalists:
                conf_final_counts[t] += 1
 
        east_w, west_w = conf_winners["East"], conf_winners["West"]
        higher = east_w if elo.get_rating(east_w) >= elo.get_rating(west_w) else west_w
        lower = west_w if higher == east_w else east_w
        champ = higher if rng.random() < _series_prob(higher, lower) else lower
        title_counts[champ] += 1
 
    results = []
    for t in teams:
        results.append({
            "team_id": t,
            "conference": conf_of[t],
            "conference_finals_probability": round(conf_final_counts[t] / n_simulations, 4),
            "finals_probability": round(finals_counts[t] / n_simulations, 4),
            "title_probability": round(title_counts[t] / n_simulations, 4),
        })
    results.sort(key=lambda x: x["title_probability"], reverse=True)
    return {"n_simulations": n_simulations, "teams": results}