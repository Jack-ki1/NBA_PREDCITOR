"""

Configuration settings for the NBA Predictor.
 
Central place for tunable model parameters:
  - Elo rating system constants (K-factor, home-court advantage, season carry-over)
  - Feature weights blended into the matchup rating adjustment
  - Monte Carlo simulation parameters
  - League structure (conferences / divisions)
"""
 
from typing import Any, Dict
 
from pydantic import BaseModel
 
# ── Elo system ───────────────────────────────────────────────────────────────
# Loosely follows the well-known FiveThirtyEight NBA Elo methodology.
ELO_BASE_RATING = 1500.0          # Rating assigned to a brand-new / average team
ELO_K_FACTOR = 20.0               # Sensitivity of a single game's rating update
ELO_HOME_ADVANTAGE = 100.0        # Elo points added to the home side (~3.5 pts)
ELO_SEASON_CARRYOVER = 0.75       # Fraction of rating carried into a new season
ELO_POINTS_PER_100 = 28.0         # Elo points ≈ 1 point of scoring margin
 
# ── Scoring / margin model ───────────────────────────────────────────────────
LEAGUE_AVG_PACE = 99.0            # Possessions per 48 minutes (league baseline)
LEAGUE_AVG_ORTG = 114.0           # Points scored per 100 possessions
MARGIN_STD = 12.0                 # Std dev of final margin around expectation
TOTAL_STD = 15.0                  # Std dev of combined points total
 
# Rest / schedule effects (points added to expected margin).
REST_ADVANTAGE_PER_DAY = 0.7      # Extra margin per additional day of rest vs opp
BACK_TO_BACK_PENALTY = 2.2        # Margin penalty for a team on the second night
 
# ── Feature weights ──────────────────────────────────────────────────────────
# These weights scale each feature's contribution (in *points*) to the expected
# home margin, on top of the pure Elo expectation.
FEATURE_WEIGHTS: Dict[str, float] = {
    "elo_diff": 1.00,          # Baseline Elo-implied margin (kept at full weight)
    "net_rating_diff": 0.35,   # Season net-rating gap (off - def per 100)
    "recent_form": 0.25,       # Momentum from last-N games
    "rest_advantage": 0.60,    # Days-rest differential effect
    "home_court": 1.00,        # Home-court advantage term
}
 
# ── Simulation parameters ────────────────────────────────────────────────────
DEFAULT_N_SIMULATIONS = 10000
MIN_SIMULATIONS = 100
MAX_SIMULATIONS = 200000
 
# ── Recent form ──────────────────────────────────────────────────────────────
RECENCY_WINDOW = 10               # Number of recent games used for form
RECENCY_DECAY = 0.92              # Exponential decay applied to older games
 
# ── Confidence thresholds (on home win probability distance from 0.5) ─────────
HIGH_CONFIDENCE_THRESHOLD = 0.68  # |win prob| beyond this ⇒ high confidence
MEDIUM_CONFIDENCE_THRESHOLD = 0.57
 
# ── League structure ─────────────────────────────────────────────────────────
CONFERENCES: Dict[str, list] = {
    "East": [
        "BOS", "NYK", "MIL", "CLE", "ORL", "IND", "PHI", "MIA",
        "CHI", "ATL", "BKN", "TOR", "CHA", "WAS", "DET",
    ],
    "West": [
        "OKC", "DEN", "MIN", "LAC", "DAL", "PHX", "LAL", "NOP",
        "SAC", "GSW", "HOU", "SAS", "UTA", "MEM", "POR",
    ],
}
 
# Playoff format: top 6 per conference auto-qualify, seeds 7-10 play-in.
PLAYOFF_TEAMS_PER_CONF = 8
PLAYIN_TEAMS_PER_CONF = 10
 
 
def get_conference(team_id: str) -> str:
    """Return the conference ('East'/'West') for a team abbreviation."""
    for conf, teams in CONFERENCES.items():
        if team_id in teams:
            return conf
    return "Unknown"
 
 
def validate_settings() -> Dict[str, Any]:
    """Sanity-check configuration values and report any problems."""
    errors = []
    if ELO_K_FACTOR <= 0:
        errors.append(f"ELO_K_FACTOR must be positive, got {ELO_K_FACTOR}")
    if not (MIN_SIMULATIONS <= DEFAULT_N_SIMULATIONS <= MAX_SIMULATIONS):
        errors.append("DEFAULT_N_SIMULATIONS outside [MIN, MAX] bounds")
    total_teams = sum(len(t) for t in CONFERENCES.values())
    if total_teams != 30:
        errors.append(f"Expected 30 teams across conferences, found {total_teams}")
    return {"valid": len(errors) == 0, "errors": errors, "team_count": total_teams}
 
 
class Settings(BaseModel):
    """Pydantic view of the settings for programmatic access/validation."""
 
    elo_base_rating: float = ELO_BASE_RATING
    elo_k_factor: float = ELO_K_FACTOR
    elo_home_advantage: float = ELO_HOME_ADVANTAGE
    feature_weights: Dict[str, float] = FEATURE_WEIGHTS
    default_simulations: int = DEFAULT_N_SIMULATIONS
    recency_window: int = RECENCY_WINDOW
 
 
settings = Settings()
 
 
__all__ = [
    "ELO_BASE_RATING",
    "ELO_K_FACTOR",
    "ELO_HOME_ADVANTAGE",
    "ELO_SEASON_CARRYOVER",
    "ELO_POINTS_PER_100",
    "LEAGUE_AVG_PACE",
    "LEAGUE_AVG_ORTG",
    "MARGIN_STD",
    "TOTAL_STD",
    "REST_ADVANTAGE_PER_DAY",
    "BACK_TO_BACK_PENALTY",
    "FEATURE_WEIGHTS",
    "DEFAULT_N_SIMULATIONS",
    "MIN_SIMULATIONS",
    "MAX_SIMULATIONS",
    "RECENCY_WINDOW",
    "RECENCY_DECAY",
    "HIGH_CONFIDENCE_THRESHOLD",
    "MEDIUM_CONFIDENCE_THRESHOLD",
    "CONFERENCES",
    "PLAYOFF_TEAMS_PER_CONF",
    "PLAYIN_TEAMS_PER_CONF",
    "get_conference",
    "validate_settings",
    "Settings",
    "settings",
]