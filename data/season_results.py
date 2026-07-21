"""
Completed-game results for the current season.

Used by the Elo engine to replay finished games on top of the static
pre-season ratings, and by feature engineering for recent-form fallbacks.

Each entry: {"date", "home", "away", "home_score", "away_score"}.
This is a representative early-season slate; extend it as more games finish.
"""

from typing import Any, Dict, List
from .api_client import NBAApiClient

# Default static season results as fallback
STATIC_SEASON_RESULTS: List[Dict[str, Any]] = [
    {"date": "2025-10-22", "home": "OKC", "away": "HOU", "home_score": 121, "away_score": 110},
    {"date": "2025-10-22", "home": "LAL", "away": "GSW", "home_score": 118, "away_score": 112},
    {"date": "2025-10-23", "home": "BOS", "away": "NYK", "home_score": 124, "away_score": 116},
    {"date": "2025-10-23", "home": "CLE", "away": "IND", "home_score": 130, "away_score": 121},
    {"date": "2025-10-24", "home": "DEN", "away": "MIN", "home_score": 115, "away_score": 108},
    {"date": "2025-10-24", "home": "MIL", "away": "PHI", "home_score": 119, "away_score": 111},
    {"date": "2025-10-25", "home": "DAL", "away": "SAS", "home_score": 112, "away_score": 105},
    {"date": "2025-10-25", "home": "MEM", "away": "UTA", "home_score": 128, "away_score": 109},
    {"date": "2025-10-26", "home": "LAC", "away": "PHX", "home_score": 109, "away_score": 114},
    {"date": "2025-10-26", "home": "ORL", "away": "MIA", "home_score": 104, "away_score": 101},
    {"date": "2025-10-27", "home": "OKC", "away": "DEN", "home_score": 123, "away_score": 118},
    {"date": "2025-10-27", "home": "NYK", "away": "CHI", "home_score": 117, "away_score": 106},
    {"date": "2025-10-28", "home": "BOS", "away": "MIL", "home_score": 122, "away_score": 114},
    {"date": "2025-10-28", "home": "HOU", "away": "SAC", "home_score": 111, "away_score": 108},
    {"date": "2025-10-29", "home": "CLE", "away": "ATL", "home_score": 126, "away_score": 118},
    {"date": "2025-10-29", "home": "MIN", "away": "POR", "home_score": 120, "away_score": 102},
    {"date": "2025-10-30", "home": "LAL", "away": "NOP", "home_score": 116, "away_score": 110},
    {"date": "2025-10-30", "home": "GSW", "away": "WAS", "home_score": 131, "away_score": 112},
    {"date": "2025-10-31", "home": "DAL", "away": "MEM", "home_score": 118, "away_score": 121},
    {"date": "2025-10-31", "home": "PHX", "away": "CHA", "home_score": 122, "away_score": 105},
    {"date": "2025-11-01", "home": "IND", "away": "DET", "home_score": 125, "away_score": 122},
    {"date": "2025-11-01", "home": "PHI", "away": "TOR", "home_score": 109, "away_score": 104},
    {"date": "2025-11-02", "home": "OKC", "away": "MIN", "home_score": 117, "away_score": 109},
    {"date": "2025-11-02", "home": "BOS", "away": "MIA", "home_score": 120, "away_score": 108},
    {"date": "2025-11-03", "home": "CLE", "away": "NYK", "home_score": 118, "away_score": 121},
    {"date": "2025-11-03", "home": "DEN", "away": "LAC", "home_score": 124, "away_score": 116},
    {"date": "2025-11-04", "home": "HOU", "away": "DAL", "home_score": 113, "away_score": 107},
    {"date": "2025-11-04", "home": "MEM", "away": "LAL", "home_score": 122, "away_score": 118},
    {"date": "2025-11-05", "home": "MIL", "away": "ATL", "home_score": 128, "away_score": 120},
    {"date": "2025-11-05", "home": "SAC", "away": "POR", "home_score": 119, "away_score": 111},
    {"date": "2025-11-06", "home": "ORL", "away": "CHA", "home_score": 108, "away_score": 96},
    {"date": "2025-11-06", "home": "UTA", "away": "WAS", "home_score": 114, "away_score": 118},
    {"date": "2025-11-07", "home": "NYK", "away": "IND", "home_score": 123, "away_score": 119},
    {"date": "2025-11-07", "home": "BKN", "away": "TOR", "home_score": 102, "away_score": 106},
    {"date": "2025-11-08", "home": "OKC", "away": "LAC", "home_score": 126, "away_score": 113},
    {"date": "2025-11-08", "home": "PHX", "away": "SAS", "home_score": 117, "away_score": 112},
    {"date": "2025-11-09", "home": "DEN", "away": "GSW", "home_score": 121, "away_score": 117},
    {"date": "2025-11-09", "home": "MIA", "away": "DET", "home_score": 110, "away_score": 104},
    {"date": "2025-11-10", "home": "BOS", "away": "PHI", "home_score": 119, "away_score": 105},
    {"date": "2025-11-10", "home": "CLE", "away": "CHI", "home_score": 127, "away_score": 115},
]

SEASON = 2026

# Global cache for season results
_season_results = None

def _ensure_season_results_loaded() -> List[Dict[str, Any]]:
    """Load season results from API if available, otherwise use static data"""
    global _season_results
    if _season_results is not None:
        return _season_results
    
    # Try to fetch live data from API
    try:
        from .api_client import sync_with_live_data
        live_data = sync_with_live_data()
        live_games = live_data.get('games', [])
        
        if live_games:
            # Use live data if available
            _season_results = live_games
        else:
            # Fall back to static data if live data is empty
            _season_results = list(STATIC_SEASON_RESULTS)
    except ImportError:
        # If nba-api is not installed, use static data
        _season_results = list(STATIC_SEASON_RESULTS)
    except Exception as e:
        print(f"Warning: Could not fetch live results, using static data: {e}")
        _season_results = list(STATIC_SEASON_RESULTS)
    
    return _season_results


def get_completed_games() -> List[Dict[str, Any]]:
    """Return all finished games in chronological order."""
    season_results = _ensure_season_results_loaded()
    return list(season_results)


def get_team_record(team_id: str) -> Dict[str, int]:
    """Compute wins/losses for a team from completed games."""
    team_id = team_id.upper()
    wins = losses = 0
    season_results = _ensure_season_results_loaded()
    for g in season_results:
        if g["home"] == team_id:
            wins += g["home_score"] > g["away_score"]
            losses += g["home_score"] < g["away_score"]
        elif g["away"] == team_id:
            wins += g["away_score"] > g["home_score"]
            losses += g["away_score"] < g["home_score"]
    return {"wins": wins, "losses": losses}


def get_team_recent_results(team_id: str, n: int = 10) -> List[int]:
    """Return point differentials (team perspective) for a team's last n games.

    Most-recent game first. Positive = win margin, negative = loss margin.
    """
    team_id = team_id.upper()
    diffs: List[int] = []
    season_results = _ensure_season_results_loaded()
    for g in season_results:
        if g["home"] == team_id:
            diffs.append(g["home_score"] - g["away_score"])
        elif g["away"] == team_id:
            diffs.append(g["away_score"] - g["home_score"])
    return list(reversed(diffs))[:n]