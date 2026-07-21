"""
NBA Predictor — CLI entry point.
 
Commands:
  predict         Predict a single game (win prob, projected score, spread, O/U)
  h2h             Neutral-court head-to-head team comparison
  series          Simulate a best-of-7 playoff series
  standings-sim   Simulate the remaining season → win totals & playoff odds
  title-odds      Simulate the playoff bracket → conference / Finals / title odds
  teams           List all teams and current Elo ratings
  migrate-db      Create the SQLite database from static data
  accuracy-report Show stored-prediction accuracy metrics
  dashboard       Launch the Flask web dashboard
  sync-data       Fetch latest data from NBA APIs
"""
 
import os
import sys
 
# Ensure the package root is importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
import json  # noqa: E402
 
import click  # noqa: E402
from rich import box  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402
 
console = Console()
 
 
@click.group()
def cli():
    """🏀 NBA Game & Season Prediction System."""
 
 
# ── predict ──────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--home", "-h", required=True, help="Home team abbreviation (e.g. BOS)")
@click.option("--away", "-a", required=True, help="Away team abbreviation (e.g. LAL)")
@click.option("--rest-home", type=int, default=None, help="Home team days of rest")
@click.option("--rest-away", type=int, default=None, help="Away team days of rest")
@click.option("--neutral", is_flag=True, help="Neutral court (no home advantage)")
@click.option("--sims", "-n", type=int, default=10000, help="Monte Carlo simulations")
@click.option("--seed", type=int, default=None, help="Random seed")
@click.option("--spread", type=float, default=None, help="Home spread line (e.g. -6.5)")
@click.option("--total", "total_line", type=float, default=None, help="Over/under total")
@click.option("--json-out", is_flag=True, help="Emit raw JSON")
@click.option("--store", is_flag=True, help="Store prediction in the database")
def predict(home, away, rest_home, rest_away, neutral, sims, seed, spread, total_line, json_out, store):
    """Predict a single game."""
    from engine.predictor import GamePredictionRequest, predict_game
 
    try:
        result = predict_game(GamePredictionRequest(
            home_id=home, away_id=away, rest_home=rest_home, rest_away=rest_away,
            neutral=neutral, n_simulations=sims, seed=seed, spread=spread, total_line=total_line,
        ))
    except KeyError as e:
        console.print(f"[red]Unknown team:[/] {e}")
        sys.exit(1)
 
    if json_out:
        click.echo(json.dumps(result, indent=2))
        return
 
    p = result["prediction"]
    meta = result["meta"]
    console.print(Panel(
        f"[bold]{meta['away_team']}[/] @ [bold]{meta['home_team']}[/]"
        f"{'  (neutral court)' if neutral else ''}\n"
        f"Simulations: {meta['n_simulations']:,}   Confidence: [green]{meta['confidence']}[/]",
        title="Matchup",
    ))
 
    t = Table(box=box.SIMPLE_HEAD, header_style="bold cyan")
    t.add_column("Team"); t.add_column("Win %", justify="right")
    t.add_column("Proj. Score", justify="right")
    t.add_row(f"{result['home']['name']} (H)", f"{p['home_win_probability']*100:.1f}%", f"{p['projected_home_score']:.1f}")
    t.add_row(f"{result['away']['name']} (A)", f"{p['away_win_probability']*100:.1f}%", f"{p['projected_away_score']:.1f}")
    console.print(t)
 
    console.print(f"\nProjected margin (home): [bold]{p['expected_margin']:+.1f}[/]  "
                  f"(80% range {p['margin_p10']:+.0f} … {p['margin_p90']:+.0f})   "
                  f"Total: [bold]{p['expected_total']:.0f}[/]")
    if "home_cover_probability" in p:
        console.print(f"ATS ({p['spread']:+.1f}): home covers [bold]{p['home_cover_probability']*100:.1f}%[/]")
    if "over_probability" in p:
        console.print(f"O/U ({p['total_line']:.1f}): over [bold]{p['over_probability']*100:.1f}%[/]")
 
    if store:
        from engine.prediction_tracker import PredictionTracker
        tracker = PredictionTracker()
        pid = tracker.store_prediction(result)
        tracker.close()
        console.print(f"[green]✓ Stored prediction #{pid}[/]")
    console.print()
 
 
# ── h2h ──────────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--team1", "-t1", required=True)
@click.option("--team2", "-t2", required=True)
def h2h(team1, team2):
    """Neutral-court head-to-head comparison based on Elo."""
    from engine.elo import get_elo_system
 
    elo = get_elo_system()
    try:
        cmp = elo.compare(team1.upper(), team2.upper(), neutral=True)
    except Exception as e:
        console.print(f"[red]Comparison failed:[/] {e}")
        sys.exit(1)
    console.print(Panel(
        f"[bold]{team1.upper()}[/] win prob: [green]{cmp['team1_win_probability']*100:.1f}%[/]\n"
        f"[bold]{team2.upper()}[/] win prob: [yellow]{cmp['team2_win_probability']*100:.1f}%[/]\n"
        f"Elo gap: {cmp['rating_difference']:+.0f}",
        title="Head-to-Head (neutral)",
    ))
 
 
# ── series ───────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--team1", "-t1", required=True, help="Higher seed (hosts 2-2-1-1-1)")
@click.option("--team2", "-t2", required=True)
@click.option("--sims", "-n", type=int, default=10000)
@click.option("--seed", type=int, default=None)
def series(team1, team2, sims, seed):
    """Simulate a best-of-7 playoff series."""
    from engine.probability_model import simulate_series
 
    r = simulate_series(team1.upper(), team2.upper(), n_simulations=sims, seed=seed)
    console.print(Panel(
        f"[bold]{team1.upper()}[/]: [green]{r['team1_series_win_probability']*100:.1f}%[/]\n"
        f"[bold]{team2.upper()}[/]: [yellow]{r['team2_series_win_probability']*100:.1f}%[/]",
        title="Best-of-7 Series",
    ))
 
 
# ── standings-sim ────────────────────────────────────────────────────────────
@cli.command("standings-sim")
@click.option("--sims", "-n", type=int, default=2000)
@click.option("--seed", type=int, default=None)
@click.option("--conference", "-c", type=click.Choice(["East", "West", "all"]), default="all")
def standings_sim(sims, seed, conference):
    """Simulate the remaining season for projected wins & playoff odds."""
    from engine.season_simulator import simulate_regular_season
 
    with console.status(f"Simulating {sims:,} seasons…"):
        res = simulate_regular_season(n_simulations=sims, seed=seed)
    rows = res["standings"]
    if conference != "all":
        rows = [r for r in rows if r["conference"] == conference]
 
    t = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", title=f"Projected Standings ({conference})")
    t.add_column("Team"); t.add_column("Conf"); t.add_column("Cur W", justify="right")
    t.add_column("Proj W", justify="right"); t.add_column("Playoff %", justify="right")
    t.add_column("Top Seed %", justify="right")
    for r in rows:
        t.add_row(r["team_id"], r["conference"], str(r["current_wins"]),
                  f"{r['projected_wins']:.1f}", f"{r['playoff_probability']*100:.1f}%",
                  f"{r['top_seed_probability']*100:.1f}%")
    console.print(t)
 
 
# ── title-odds ───────────────────────────────────────────────────────────────
@cli.command("title-odds")
@click.option("--sims", "-n", type=int, default=2000)
@click.option("--seed", type=int, default=None)
@click.option("--top", type=int, default=12, help="Show top N teams")
def title_odds(sims, seed, top):
    """Simulate the playoff bracket for conference / Finals / title odds."""
    from engine.season_simulator import simulate_playoffs
 
    with console.status(f"Simulating {sims:,} playoff brackets…"):
        res = simulate_playoffs(n_simulations=sims, seed=seed)
 
    t = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", title="Championship Odds")
    t.add_column("Team"); t.add_column("Conf")
    t.add_column("Conf Finals %", justify="right"); t.add_column("Finals %", justify="right")
    t.add_column("Title %", justify="right")
    for r in res["teams"][:top]:
        t.add_row(r["team_id"], r["conference"],
                  f"{r['conference_finals_probability']*100:.1f}%",
                  f"{r['finals_probability']*100:.1f}%",
                  f"{r['title_probability']*100:.1f}%")
    console.print(t)
 
 
# ── teams ────────────────────────────────────────────────────────────────────
@cli.command()
def teams():
    """List all teams with current Elo ratings and records."""
    from data.season_results import get_team_record
    from data.team_data import get_all_teams
    from engine.elo import get_elo_system
 
    elo = get_elo_system()
    rows = sorted(get_all_teams(), key=lambda x: elo.get_rating(x["id"]), reverse=True)
    t = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", title="NBA Teams by Elo")
    t.add_column("#", justify="right"); t.add_column("Team"); t.add_column("Conf")
    t.add_column("Elo", justify="right"); t.add_column("Record", justify="right")
    for i, team in enumerate(rows, 1):
        rec = get_team_record(team["id"])
        t.add_row(str(i), f"{team['id']} · {team['name']}", team["conference"],
                  f"{elo.get_rating(team['id']):.0f}", f"{rec['wins']}-{rec['losses']}")
    console.print(t)
 
 
# ── migrate-db ───────────────────────────────────────────────────────────────
@cli.command("migrate-db")
def migrate_db():
    """Create the SQLite database and load static team/game data."""
    from database.models import migrate_from_static
 
    migrate_from_static()
    console.print("[green]✓ Database created and populated.[/]")
 
 
# ── accuracy-report ──────────────────────────────────────────────────────────
@cli.command("accuracy-report")
def accuracy_report():
    """Show accuracy metrics for stored predictions."""
    from engine.prediction_tracker import PredictionTracker
 
    tracker = PredictionTracker()
    rep = tracker.get_accuracy_report()
    tracker.close()
    console.print(Panel(
        f"Total predictions: [bold]{rep['total_predictions']}[/]\n"
        f"Evaluated: [bold]{rep['evaluated_predictions']}[/]\n"
        f"Avg Brier score: [bold]{rep['avg_brier_score']}[/]\n"
        f"Hit rate: [bold]{rep['hit_rate']}[/]",
        title="Accuracy",
    ))
 
 
# ── sync-data ────────────────────────────────────────────────────────────────
@cli.command("sync-data")
def sync_data():
    """Fetch latest data from NBA APIs."""
    from data.synchronizer import update_local_data
    console.print("[cyan]Syncing latest NBA data...[/]")
    try:
        data = update_local_data()
        console.print(f"[green]✓ Synced {len(data['games'])} games and {len(data['team_stats'])} teams[/]")
    except Exception as e:
        console.print(f"[red]✗ Sync failed:[/] {e}")
 
 
# ── dashboard ────────────────────────────────────────────────────────────────
@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", "-p", type=int, default=5001)
@click.option("--debug", is_flag=True)
def dashboard(host, port, debug):
    """Launch the Flask web dashboard."""
    from dashboard.app import app
 
    console.print(f"[bold cyan]NBA Predictor Dashboard[/] → http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
 
 
if __name__ == "__main__":
    cli()