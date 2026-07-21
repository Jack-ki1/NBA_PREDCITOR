"""
Team Elo rating system for the NBA.
 
Implements a FiveThirtyEight-style Elo model:
  - Home-court advantage applied to the home side's expected result.
  - Margin-of-victory (MOV) multiplier so blowouts move ratings more, with a
    correction that dampens rating inflation for already-strong favourites.
  - Season carry-over that regresses ratings toward the mean between seasons.
 
The module exposes a lazily-initialised singleton (`get_elo_system`) that seeds
ratings from the static team profiles and replays all completed games.
"""
 
import math
from typing import Dict, List, Optional
 
from config.settings import (
    ELO_BASE_RATING,
    ELO_HOME_ADVANTAGE,
    ELO_K_FACTOR,
    ELO_POINTS_PER_100,
    ELO_SEASON_CARRYOVER,
)
 
 
class TeamEloSystem:
    """Tracks and updates a single Elo rating per team."""
 
    def __init__(
        self,
        k_factor: float = ELO_K_FACTOR,
        home_advantage: float = ELO_HOME_ADVANTAGE,
    ):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.ratings: Dict[str, float] = {}
 
    # ── setup ────────────────────────────────────────────────────────────────
    def initialize_team(self, team_id: str, rating: float = ELO_BASE_RATING) -> None:
        self.ratings[team_id] = float(rating)
 
    def get_rating(self, team_id: str) -> float:
        return self.ratings.get(team_id, ELO_BASE_RATING)
 
    # ── probabilities ─────────────────────────────────────────────────────────
    def expected_home_win_prob(self, home_id: str, away_id: str, neutral: bool = False) -> float:
        """Win probability for the home team given current ratings."""
        hca = 0.0 if neutral else self.home_advantage
        diff = self.get_rating(home_id) + hca - self.get_rating(away_id)
        return 1.0 / (1.0 + 10 ** (-diff / 400.0))
 
    def expected_margin(self, home_id: str, away_id: str, neutral: bool = False) -> float:
        """Elo-implied expected point margin (home - away)."""
        hca = 0.0 if neutral else self.home_advantage
        diff = self.get_rating(home_id) + hca - self.get_rating(away_id)
        return diff / ELO_POINTS_PER_100
 
    # ── updates ────────────────────────────────────────────────────────────────
    @staticmethod
    def _mov_multiplier(margin: int, elo_diff_winner: float) -> float:
        """FiveThirtyEight margin-of-victory multiplier.
 
        `elo_diff_winner` is (winner_rating_incl_hca - loser_rating_incl_hca).
        The denominator correction prevents strong favourites from gaining
        outsized rating for beating weak opponents.
        """
        return (abs(margin) + 3.0) ** 0.8 / (7.5 + 0.006 * elo_diff_winner)
 
    def update_game(
        self,
        home_id: str,
        away_id: str,
        home_score: int,
        away_score: int,
        neutral: bool = False,
    ) -> Dict[str, float]:
        """Update both teams' ratings after a completed game."""
        if home_id not in self.ratings:
            self.initialize_team(home_id)
        if away_id not in self.ratings:
            self.initialize_team(away_id)
 
        hca = 0.0 if neutral else self.home_advantage
        home_eff = self.ratings[home_id] + hca
        away_eff = self.ratings[away_id]
 
        exp_home = 1.0 / (1.0 + 10 ** (-(home_eff - away_eff) / 400.0))
        margin = home_score - away_score
        home_won = margin > 0
        result_home = 1.0 if home_won else 0.0
 
        # Winner's effective-rating edge (>=0 keeps multiplier well-behaved).
        if home_won:
            elo_diff_winner = home_eff - away_eff
        else:
            elo_diff_winner = away_eff - home_eff
        mov_mult = self._mov_multiplier(margin, elo_diff_winner)
 
        delta = self.k_factor * mov_mult * (result_home - exp_home)
        self.ratings[home_id] += delta
        self.ratings[away_id] -= delta
        return {home_id: self.ratings[home_id], away_id: self.ratings[away_id]}
 
    def apply_season_carryover(self) -> None:
        """Regress every rating toward the league mean between seasons."""
        for tid, rating in self.ratings.items():
            self.ratings[tid] = (
                ELO_SEASON_CARRYOVER * rating
                + (1 - ELO_SEASON_CARRYOVER) * ELO_BASE_RATING
            )
 
    def rankings(self) -> List[Dict[str, float]]:
        """Teams sorted by rating, highest first."""
        return [
            {"team_id": tid, "rating": round(r, 1)}
            for tid, r in sorted(self.ratings.items(), key=lambda kv: kv[1], reverse=True)
        ]
 
    def compare(self, team1: str, team2: str, neutral: bool = True) -> Dict[str, float]:
        """Neutral-court head-to-head win probability and rating gap."""
        p1 = self.expected_home_win_prob(team1, team2, neutral=neutral)
        return {
            "team1": team1,
            "team2": team2,
            "team1_win_probability": round(p1, 4),
            "team2_win_probability": round(1 - p1, 4),
            "rating_difference": round(self.get_rating(team1) - self.get_rating(team2), 1),
        }
 
 
# ── Singleton ────────────────────────────────────────────────────────────────
_elo_system: Optional[TeamEloSystem] = None
 
 
def get_elo_system(force_rebuild: bool = False) -> TeamEloSystem:
    """Return the shared Elo system, seeding + replaying games on first use."""
    global _elo_system
    if _elo_system is not None and not force_rebuild:
        return _elo_system
 
    system = TeamEloSystem()
 
    from data.team_data import get_all_teams
    for team in get_all_teams():
        system.initialize_team(team["id"], team.get("elo", ELO_BASE_RATING))
 
    # Replay completed games to move ratings from pre-season toward current form.
    from data.season_results import get_completed_games
    for game in get_completed_games():
        system.update_game(
            game["home"], game["away"], game["home_score"], game["away_score"]
        )
 
    _elo_system = system
    return _elo_system
 
 
def reset_elo_system() -> None:
    """Drop the cached singleton (useful for tests)."""
    global _elo_system
    _elo_system = None