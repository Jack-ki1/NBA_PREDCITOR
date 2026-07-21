"""
Prediction orchestrator.
 
Wraps the Monte Carlo game model with a request/response contract, result
caching, and confidence labelling — the NBA analogue of the F1 predictor.
"""
 
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
 
from config.settings import (
    DEFAULT_N_SIMULATIONS,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
)
from data.team_data import get_team
from engine.probability_model import simulate_game
 
MODEL_VERSION = "1.0.0"
 
 
@dataclass
class GamePredictionRequest:
    home_id: str
    away_id: str
    rest_home: Optional[int] = None
    rest_away: Optional[int] = None
    neutral: bool = False
    n_simulations: int = DEFAULT_N_SIMULATIONS
    seed: Optional[int] = None
    spread: Optional[float] = None
    total_line: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)
 
 
_cache: Dict[str, dict] = {}
_cache_ttl: Dict[str, float] = {}
CACHE_TTL_SECONDS = 300
 
 
def _cache_key(req: GamePredictionRequest) -> str:
    payload = {
        "home": req.home_id.upper(),
        "away": req.away_id.upper(),
        "rest_home": req.rest_home,
        "rest_away": req.rest_away,
        "neutral": req.neutral,
        "sims": req.n_simulations,
        "seed": req.seed,
        "spread": req.spread,
        "total": req.total_line,
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
 
 
def _confidence(win_prob: float) -> str:
    edge = max(win_prob, 1 - win_prob)
    if edge >= HIGH_CONFIDENCE_THRESHOLD:
        return "High"
    if edge >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "Medium"
    return "Low"
 
 
def predict_game(req: GamePredictionRequest) -> Dict[str, Any]:
    """Run a cached game prediction and attach presentation metadata."""
    key = _cache_key(req)
    now = time.monotonic()
    if key in _cache and now - _cache_ttl[key] < CACHE_TTL_SECONDS:
        return _cache[key]
 
    sim = simulate_game(
        home_id=req.home_id,
        away_id=req.away_id,
        rest_home=req.rest_home,
        rest_away=req.rest_away,
        neutral=req.neutral,
        n_simulations=req.n_simulations,
        seed=req.seed,
        spread=req.spread,
        total_line=req.total_line,
    )
 
    home = get_team(sim["home_id"])
    away = get_team(sim["away_id"])
    home_win = sim["home_win_probability"]
    favourite = sim["home_id"] if home_win >= 0.5 else sim["away_id"]
 
    result = {
        "meta": {
            "model_version": MODEL_VERSION,
            "home_team": home["name"],
            "away_team": away["name"],
            "neutral_court": req.neutral,
            "n_simulations": req.n_simulations,
            "confidence": _confidence(home_win),
            "favourite": favourite,
        },
        "prediction": sim,
        "home": {"id": home["id"], "name": home["name"], "conference": home["conference"]},
        "away": {"id": away["id"], "name": away["name"], "conference": away["conference"]},
    }
 
    _cache[key] = result
    _cache_ttl[key] = now
    return result
 
 
def clear_cache() -> None:
    _cache.clear()
    _cache_ttl.clear()