"""
Upcoming game schedule and remaining-season fixture generation.
 
`UPCOMING_GAMES` is a curated near-term slate used by the dashboard and CLI
for concrete matchups. `generate_remaining_schedule` produces a balanced
round-robin fixture list used by the season simulator for standings / title
odds when a full official schedule is not loaded.
"""
 
from typing import Any, Dict, List, Optional
 
from .team_data import TEAMS
 
# rest_home / rest_away = days of rest before the game (1 == back-to-back).
UPCOMING_GAMES: List[Dict[str, Any]] = [
    {"id": "g1", "date": "2025-11-12", "home": "OKC", "away": "DEN", "rest_home": 2, "rest_away": 2},
    {"id": "g2", "date": "2025-11-12", "home": "BOS", "away": "CLE", "rest_home": 2, "rest_away": 1},
    {"id": "g3", "date": "2025-11-12", "home": "NYK", "away": "MIL", "rest_home": 1, "rest_away": 2},
    {"id": "g4", "date": "2025-11-13", "home": "LAL", "away": "MEM", "rest_home": 2, "rest_away": 2},
    {"id": "g5", "date": "2025-11-13", "home": "DEN", "away": "MIN", "rest_home": 1, "rest_away": 3},
    {"id": "g6", "date": "2025-11-13", "home": "HOU", "away": "DAL", "rest_home": 2, "rest_away": 1},
    {"id": "g7", "date": "2025-11-14", "home": "PHX", "away": "LAC", "rest_home": 3, "rest_away": 2},
    {"id": "g8", "date": "2025-11-14", "home": "MIA", "away": "ORL", "rest_home": 2, "rest_away": 2},
    {"id": "g9", "date": "2025-11-14", "home": "IND", "away": "PHI", "rest_home": 1, "rest_away": 2},
    {"id": "g10", "date": "2025-11-15", "home": "GSW", "away": "SAC", "rest_home": 2, "rest_away": 1},
    {"id": "g11", "date": "2025-11-15", "home": "ATL", "away": "CHI", "rest_home": 2, "rest_away": 2},
    {"id": "g12", "date": "2025-11-15", "home": "DET", "away": "TOR", "rest_home": 1, "rest_away": 2},
]
 
 
def get_upcoming_games() -> List[Dict[str, Any]]:
    """Return the curated near-term slate."""
    return list(UPCOMING_GAMES)
 
 
def get_game(game_id: str) -> Optional[Dict[str, Any]]:
    """Look up a curated game by id."""
    for g in UPCOMING_GAMES:
        if g["id"] == game_id:
            return g
    return None
 
 
def generate_remaining_schedule(games_per_pair: int = 2) -> List[Dict[str, str]]:
    """Generate a balanced remaining-season fixture list.
 
    For each unordered pair of teams, schedules `games_per_pair` games,
    alternating home/away so home games are split evenly. Deterministic.
    """
    team_ids = list(TEAMS.keys())
    fixtures: List[Dict[str, str]] = []
    for i, home in enumerate(team_ids):
        for away in team_ids[i + 1:]:
            for k in range(games_per_pair):
                # Alternate host each meeting for balance.
                if k % 2 == 0:
                    fixtures.append({"home": home, "away": away})
                else:
                    fixtures.append({"home": away, "away": home})
    return fixtures