"""
Standalone HTML report generator for a single game prediction.
 
Produces a self-contained HTML file (Plotly loaded from CDN) that can be opened
in any browser or shared — the NBA analogue of the F1 HTML report.
"""
 
import json
import os
from datetime import datetime
from typing import Optional
 
from engine.predictor import GamePredictionRequest, predict_game
 
 
def generate_report(
    home_id: str,
    away_id: str,
    n_simulations: int = 10000,
    output_dir: str = "reports_output",
    seed: Optional[int] = None,
) -> str:
    """Generate an HTML report for a game and return the file path."""
    result = predict_game(GamePredictionRequest(
        home_id=home_id, away_id=away_id, n_simulations=n_simulations, seed=seed,
    ))
    p = result["prediction"]
    meta = result["meta"]
 
    os.makedirs(output_dir, exist_ok=True)
    fname = f"{away_id.upper()}_at_{home_id.upper()}_{datetime.now():%Y%m%d_%H%M%S}.html"
    path = os.path.join(output_dir, fname)
 
    win_data = [
        {"team": meta["home_team"], "prob": p["home_win_probability"] * 100},
        {"team": meta["away_team"], "prob": p["away_win_probability"] * 100},
    ]
 
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{meta['away_team']} @ {meta['home_team']} — NBA Prediction</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; background:#0f1116; color:#e8eaed; }}
  header {{ padding: 24px; background:#161a22; border-bottom:1px solid #2a2f3a; }}
  h1 {{ margin:0; font-size:22px; }}
  .sub {{ color:#9aa0aa; margin-top:6px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; padding:24px; }}
  .card {{ background:#161a22; border:1px solid #2a2f3a; border-radius:12px; padding:16px; }}
  .stat {{ font-size:30px; font-weight:700; }}
  .label {{ color:#9aa0aa; font-size:13px; }}
</style>
</head>
<body>
<header>
  <h1>🏀 {meta['away_team']} @ {meta['home_team']}</h1>
  <div class="sub">{n_simulations:,} Monte Carlo simulations · confidence: {meta['confidence']}
   · model v{meta['model_version']}</div>
</header>
<div class="grid">
  <div class="card"><div class="label">Home win probability</div>
    <div class="stat">{p['home_win_probability']*100:.1f}%</div></div>
  <div class="card"><div class="label">Projected score</div>
    <div class="stat">{p['projected_home_score']:.0f}–{p['projected_away_score']:.0f}</div></div>
  <div class="card"><div class="label">Projected margin (home)</div>
    <div class="stat">{p['expected_margin']:+.1f}</div></div>
  <div class="card"><div class="label">Projected total</div>
    <div class="stat">{p['expected_total']:.0f}</div></div>
</div>
<div class="grid">
  <div class="card" style="grid-column:1/-1;"><div id="winChart" style="height:320px;"></div></div>
</div>
<script>
  const win = {json.dumps(win_data)};
  Plotly.newPlot('winChart', [{{
    type:'bar', x: win.map(d=>d.team), y: win.map(d=>d.prob),
    marker:{{color:['#4c8bf5','#f55f4c']}}, text: win.map(d=>d.prob.toFixed(1)+'%'), textposition:'auto'
  }}], {{
    title:'Win Probability', paper_bgcolor:'#161a22', plot_bgcolor:'#161a22',
    font:{{color:'#e8eaed'}}, yaxis:{{title:'%', range:[0,100]}}, margin:{{t:40}}
  }}, {{displayModeBar:false, responsive:true}});
</script>
</body>
</html>"""
 
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path