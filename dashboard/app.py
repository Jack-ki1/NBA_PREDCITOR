"""
NBA Predictor web dashboard (Flask + Plotly).
 
Single-page app with a JSON API:
  GET  /                 Dashboard page
  GET  /api/teams        Teams with Elo ratings and records
  POST /api/predict      Single-game prediction
  GET  /api/standings    Remaining-season simulation (win totals, playoff odds)
  GET  /api/title-odds   Playoff bracket simulation (title odds)
  GET  /api/health       Liveness probe
"""
 
import os
import sys
from pathlib import Path
 
# Make the package root importable when app.py is run directly.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
 
from flask import Flask, jsonify, render_template, request  # noqa: E402
 
from data.season_results import get_team_record  # noqa: E402
from data.team_data import get_all_teams, team_exists  # noqa: E402
from engine.elo import get_elo_system  # noqa: E402
from engine.predictor import GamePredictionRequest, predict_game  # noqa: E402
from engine.season_simulator import simulate_playoffs, simulate_regular_season  # noqa: E402
 
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "nba-predictor-dev-key")
 
 
def _clamp_sims(value, default, lo=100, hi=200000):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))
 
 
@app.route("/")
def index():
    return render_template("dashboard.html")
 
 
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})
 
 
@app.route("/api/teams")
def api_teams():
    elo = get_elo_system()
    teams = []
    for t in sorted(get_all_teams(), key=lambda x: elo.get_rating(x["id"]), reverse=True):
        rec = get_team_record(t["id"])
        teams.append({
            "id": t["id"], "name": t["name"], "conference": t["conference"],
            "elo": round(elo.get_rating(t["id"]), 0),
            "wins": rec["wins"], "losses": rec["losses"],
        })
    return jsonify({"teams": teams})
 
 
@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    home = (data.get("home") or "").upper()
    away = (data.get("away") or "").upper()
    if not team_exists(home) or not team_exists(away):
        return jsonify({"error": "Unknown or missing team abbreviation"}), 400
    if home == away:
        return jsonify({"error": "Home and away must differ"}), 400
 
    def _num(key):
        v = data.get(key)
        return None if v in (None, "") else float(v)
 
    result = predict_game(GamePredictionRequest(
        home_id=home, away_id=away,
        rest_home=int(data["rest_home"]) if data.get("rest_home") not in (None, "") else None,
        rest_away=int(data["rest_away"]) if data.get("rest_away") not in (None, "") else None,
        neutral=bool(data.get("neutral", False)),
        n_simulations=_clamp_sims(data.get("sims"), 10000),
        seed=int(data["seed"]) if data.get("seed") not in (None, "") else None,
        spread=_num("spread"),
        total_line=_num("total"),
    ))
    return jsonify(result)
 
 
@app.route("/api/standings")
def api_standings():
    sims = _clamp_sims(request.args.get("sims"), 2000, hi=20000)
    return jsonify(simulate_regular_season(n_simulations=sims))
 
 
@app.route("/api/title-odds")
def api_title_odds():
    sims = _clamp_sims(request.args.get("sims"), 2000, hi=20000)
    return jsonify(simulate_playoffs(n_simulations=sims))
 
 
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)