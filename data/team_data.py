"""
NBA team profiles for the prediction system.

Each of the 30 franchises has:
  - Identity (abbreviation, full name, conference, division)
  - Pre-season Elo estimate (calibrated so the league mean is ~1500)
  - Season efficiency metrics: offensive rating, defensive rating, pace
  - Recent form (list of point differentials from most-recent games first)

Values are grounded in 2024-25 regular-season performance and serve as the
static baseline; the Elo engine replays completed games on top of these.
"""

from typing import Any, Dict, List
from .api_client import NBAApiClient

# Default static data as fallback
STATIC_TEAMS: Dict[str, Dict[str, Any]] = {
    # ── Eastern Conference ──────────────────────────────────────────────────
    "BOS": {"id": "BOS", "name": "Boston Celtics", "conference": "East", "division": "Atlantic",
            "elo": 1680, "off_rating": 119.5, "def_rating": 111.0, "pace": 98.5,
            "recent_form": [9, 12, -3, 15, 6, 8, -5, 11, 4, 7]},
    "NYK": {"id": "NYK", "name": "New York Knicks", "conference": "East", "division": "Atlantic",
            "elo": 1590, "off_rating": 117.3, "def_rating": 113.2, "pace": 96.8,
            "recent_form": [5, -2, 8, 6, -4, 10, 3, 7, -1, 5]},
    "MIL": {"id": "MIL", "name": "Milwaukee Bucks", "conference": "East", "division": "Central",
            "elo": 1560, "off_rating": 116.8, "def_rating": 113.9, "pace": 100.4,
            "recent_form": [6, 4, -8, 3, 9, -2, 5, 1, -3, 8]},
    "CLE": {"id": "CLE", "name": "Cleveland Cavaliers", "conference": "East", "division": "Central",
            "elo": 1620, "off_rating": 121.0, "def_rating": 111.8, "pace": 98.0,
            "recent_form": [11, 7, 13, -1, 8, 6, 10, -4, 9, 5]},
    "ORL": {"id": "ORL", "name": "Orlando Magic", "conference": "East", "division": "Southeast",
            "elo": 1520, "off_rating": 110.5, "def_rating": 109.1, "pace": 97.9,
            "recent_form": [3, -6, 5, 2, -3, 7, -1, 4, 6, -2]},
    "IND": {"id": "IND", "name": "Indiana Pacers", "conference": "East", "division": "Central",
            "elo": 1540, "off_rating": 118.2, "def_rating": 115.4, "pace": 102.6,
            "recent_form": [4, 8, -5, 6, 3, -7, 9, 2, 5, -1]},
    "PHI": {"id": "PHI", "name": "Philadelphia 76ers", "conference": "East", "division": "Atlantic",
            "elo": 1470, "off_rating": 113.4, "def_rating": 114.7, "pace": 98.2,
            "recent_form": [-4, 3, -8, 2, -5, 6, -2, 1, -6, 4]},
    "MIA": {"id": "MIA", "name": "Miami Heat", "conference": "East", "division": "Southeast",
            "elo": 1500, "off_rating": 112.0, "def_rating": 112.6, "pace": 96.1,
            "recent_form": [2, -3, 5, 1, 4, -6, 3, -2, 7, -1]},
    "CHI": {"id": "CHI", "name": "Chicago Bulls", "conference": "East", "division": "Central",
            "elo": 1440, "off_rating": 114.1, "def_rating": 116.0, "pace": 101.2,
            "recent_form": [-2, 4, -5, 3, -8, 2, -1, 5, -4, 1]},
    "ATL": {"id": "ATL", "name": "Atlanta Hawks", "conference": "East", "division": "Southeast",
            "elo": 1450, "off_rating": 113.8, "def_rating": 115.9, "pace": 101.8,
            "recent_form": [3, -5, 2, -4, 6, -2, 4, -7, 1, 3]},
    "BKN": {"id": "BKN", "name": "Brooklyn Nets", "conference": "East", "division": "Atlantic",
            "elo": 1370, "off_rating": 110.2, "def_rating": 116.8, "pace": 97.4,
            "recent_form": [-6, -3, 2, -9, 1, -4, -2, 3, -7, -1]},
    "TOR": {"id": "TOR", "name": "Toronto Raptors", "conference": "East", "division": "Atlantic",
            "elo": 1390, "off_rating": 111.5, "def_rating": 116.2, "pace": 99.7,
            "recent_form": [-4, 2, -6, -1, 3, -8, 1, -3, 4, -5]},
    "CHA": {"id": "CHA", "name": "Charlotte Hornets", "conference": "East", "division": "Southeast",
            "elo": 1330, "off_rating": 108.6, "def_rating": 117.5, "pace": 98.8,
            "recent_form": [-8, -4, -2, -10, 1, -6, -3, -5, 2, -7]},
    "WAS": {"id": "WAS", "name": "Washington Wizards", "conference": "East", "division": "Southeast",
            "elo": 1300, "off_rating": 108.0, "def_rating": 119.3, "pace": 103.1,
            "recent_form": [-11, -6, -3, -9, -5, -12, -2, -7, -4, -8]},
    "DET": {"id": "DET", "name": "Detroit Pistons", "conference": "East", "division": "Central",
            "elo": 1420, "off_rating": 112.3, "def_rating": 114.5, "pace": 100.5,
            "recent_form": [2, -3, 5, -1, 4, -6, 3, 1, -4, 6]},

    # ── Western Conference ──────────────────────────────────────────────────
    "OKC": {"id": "OKC", "name": "Oklahoma City Thunder", "conference": "West", "division": "Northwest",
            "elo": 1710, "off_rating": 119.2, "def_rating": 106.6, "pace": 100.9,
            "recent_form": [14, 9, 18, 6, 11, 8, 15, -2, 12, 10]},
    "DEN": {"id": "DEN", "name": "Denver Nuggets", "conference": "West", "division": "Northwest",
            "elo": 1600, "off_rating": 120.4, "def_rating": 114.1, "pace": 98.6,
            "recent_form": [8, 5, 11, -3, 7, 9, 4, 6, -1, 8]},
    "MIN": {"id": "MIN", "name": "Minnesota Timberwolves", "conference": "West", "division": "Northwest",
            "elo": 1580, "off_rating": 115.7, "def_rating": 110.8, "pace": 98.1,
            "recent_form": [6, 9, -2, 5, 8, 3, -4, 7, 5, 2]},
    "LAC": {"id": "LAC", "name": "Los Angeles Clippers", "conference": "West", "division": "Pacific",
            "elo": 1560, "off_rating": 115.0, "def_rating": 110.4, "pace": 96.9,
            "recent_form": [5, 7, 3, -2, 9, 4, 6, -3, 8, 1]},
    "DAL": {"id": "DAL", "name": "Dallas Mavericks", "conference": "West", "division": "Southwest",
            "elo": 1540, "off_rating": 116.2, "def_rating": 112.9, "pace": 97.5,
            "recent_form": [4, -3, 8, 5, -1, 6, 3, -5, 7, 2]},
    "PHX": {"id": "PHX", "name": "Phoenix Suns", "conference": "West", "division": "Pacific",
            "elo": 1510, "off_rating": 117.1, "def_rating": 115.3, "pace": 99.4,
            "recent_form": [3, 6, -4, 2, 5, -6, 4, 1, -2, 7]},
    "LAL": {"id": "LAL", "name": "Los Angeles Lakers", "conference": "West", "division": "Pacific",
            "elo": 1550, "off_rating": 115.9, "def_rating": 112.5, "pace": 98.3,
            "recent_form": [5, 8, -2, 6, 3, 9, -4, 5, 2, 7]},
    "NOP": {"id": "NOP", "name": "New Orleans Pelicans", "conference": "West", "division": "Southwest",
            "elo": 1440, "off_rating": 112.6, "def_rating": 115.1, "pace": 99.0,
            "recent_form": [-3, 4, -6, 2, -1, 5, -4, 3, -7, 1]},
    "SAC": {"id": "SAC", "name": "Sacramento Kings", "conference": "West", "division": "Pacific",
            "elo": 1480, "off_rating": 116.4, "def_rating": 116.7, "pace": 100.2,
            "recent_form": [2, -4, 6, 3, -2, 5, -6, 4, 1, -3]},
    "GSW": {"id": "GSW", "name": "Golden State Warriors", "conference": "West", "division": "Pacific",
            "elo": 1530, "off_rating": 115.5, "def_rating": 112.1, "pace": 100.8,
            "recent_form": [4, 7, -3, 6, 2, 8, -5, 5, 3, -1]},
    "HOU": {"id": "HOU", "name": "Houston Rockets", "conference": "West", "division": "Southwest",
            "elo": 1570, "off_rating": 114.3, "def_rating": 109.9, "pace": 99.6,
            "recent_form": [7, 5, 9, -2, 6, 4, 8, -3, 5, 6]},
    "SAS": {"id": "SAS", "name": "San Antonio Spurs", "conference": "West", "division": "Southwest",
            "elo": 1460, "off_rating": 113.0, "def_rating": 114.2, "pace": 100.1,
            "recent_form": [3, -2, 5, -4, 6, 1, -3, 4, 2, -5]},
    "UTA": {"id": "UTA", "name": "Utah Jazz", "conference": "West", "division": "Northwest",
            "elo": 1350, "off_rating": 111.4, "def_rating": 118.6, "pace": 99.8,
            "recent_form": [-7, -3, 1, -9, -4, 2, -6, -2, -5, 3]},
    "MEM": {"id": "MEM", "name": "Memphis Grizzlies", "conference": "West", "division": "Southwest",
            "elo": 1560, "off_rating": 117.8, "def_rating": 112.0, "pace": 103.4,
            "recent_form": [6, 9, 4, -2, 8, 5, 7, -3, 6, 2]},
    "POR": {"id": "POR", "name": "Portland Trail Blazers", "conference": "West", "division": "Northwest",
            "elo": 1360, "off_rating": 109.8, "def_rating": 116.4, "pace": 100.7,
            "recent_form": [-5, 2, -7, 1, -3, 4, -8, -1, 3, -6]},
}


# Export TEAMS for backward compatibility
TEAMS = STATIC_TEAMS

# Global cache for teams data
_teams_data = None

def _ensure_teams_data_loaded() -> Dict[str, Dict[str, Any]]:
    """Load teams data from API if available, otherwise use static data"""
    global _teams_data
    if _teams_data is not None:
        return _teams_data
    
    # Try to fetch live data from API
    try:
        from .api_client import sync_with_live_data
        live_data = sync_with_live_data()
        live_team_stats = live_data.get('team_stats', {})
        
        # Update static data with live stats where available
        _teams_data = {}
        for team_id, team_info in STATIC_TEAMS.items():
            updated_team = team_info.copy()
            if team_id in live_team_stats:
                live_stats = live_team_stats[team_id]
                # Update stats with live data while preserving essential keys
                updated_team.update({
                    'off_rating': live_stats.get('off_rating', team_info.get('off_rating', 110.0)),
                    'def_rating': live_stats.get('def_rating', team_info.get('def_rating', 110.0)),
                    'pace': live_stats.get('pace', team_info.get('pace', 98.0)),
                    'recent_form': live_stats.get('recent_form', team_info.get('recent_form', []))
                })
            _teams_data[team_id] = updated_team
    except ImportError:
        # If nba-api is not installed, use static data
        _teams_data = STATIC_TEAMS.copy()
    except Exception as e:
        print(f"Warning: Could not fetch live data, using static data: {e}")
        _teams_data = STATIC_TEAMS.copy()
    
    return _teams_data


def get_team(team_id: str) -> Dict[str, Any]:
    """Return a team's profile by abbreviation (case-insensitive)."""
    key = (team_id or "").upper()
    teams_data = _ensure_teams_data_loaded()
    if key not in teams_data:
        raise KeyError(f"Unknown team id: {team_id!r}")
    return teams_data[key]


def get_all_teams() -> List[Dict[str, Any]]:
    """Return all 30 team profiles."""
    teams_data = _ensure_teams_data_loaded()
    return list(teams_data.values())


def get_teams_by_conference(conference: str) -> List[Dict[str, Any]]:
    """Return teams in the given conference ('East' or 'West')."""
    teams_data = _ensure_teams_data_loaded()
    return [t for t in teams_data.values() if t["conference"].lower() == conference.lower()]


def team_exists(team_id: str) -> bool:
    teams_data = _ensure_teams_data_loaded()
    return (team_id or "").upper() in teams_data