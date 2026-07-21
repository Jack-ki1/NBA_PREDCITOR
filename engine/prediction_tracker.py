"""
Prediction tracking & accuracy reporting.
 
Stores game predictions in the database, evaluates them against actual results
using the Brier score, and aggregates accuracy metrics.
"""
 
from datetime import datetime
from typing import Any, Dict, Optional
 
from database.models import Game, Prediction, SessionLocal, create_database
 
 
class PredictionTracker:
    """Thin service over the SQLAlchemy session for prediction persistence."""
 
    def __init__(self):
        create_database()
        self.db = SessionLocal()
 
    def close(self) -> None:
        self.db.close()
 
    def store_prediction(
        self,
        result: Dict[str, Any],
        season: int = 2026,
        game_date: Optional[str] = None,
    ) -> int:
        """Persist a predictor result; returns the prediction row id."""
        pred = result["prediction"]
        home_id, away_id = pred["home_id"], pred["away_id"]
 
        game = (
            self.db.query(Game)
            .filter_by(home_id=home_id, away_id=away_id, season=season, completed=False)
            .first()
        )
        if game is None:
            game = Game(
                home_id=home_id, away_id=away_id, season=season,
                game_date=game_date, completed=False,
            )
            self.db.add(game)
            self.db.flush()
 
        row = Prediction(
            game_id=game.id,
            home_win_probability=pred["home_win_probability"],
            projected_home_score=pred["projected_home_score"],
            projected_away_score=pred["projected_away_score"],
            expected_margin=pred["expected_margin"],
            model_version=result["meta"]["model_version"],
        )
        self.db.add(row)
        self.db.commit()
        return row.id
 
    def evaluate_prediction(
        self, prediction_id: int, home_score: int, away_score: int
    ) -> Dict[str, Any]:
        """Score a stored prediction against an actual final and store the Brier score."""
        row = self.db.query(Prediction).get(prediction_id)
        if row is None:
            raise KeyError(f"Prediction {prediction_id} not found")
 
        actual_home_win = home_score > away_score
        outcome = 1.0 if actual_home_win else 0.0
        brier = (row.home_win_probability - outcome) ** 2
 
        row.actual_home_win = actual_home_win
        row.brier_score = brier
        row.evaluated_at = datetime.utcnow()
 
        game = self.db.query(Game).get(row.game_id)
        if game is not None:
            game.completed = True
            game.home_score = home_score
            game.away_score = away_score
 
        self.db.commit()
        return {"prediction_id": prediction_id, "brier_score": round(brier, 4),
                "actual_home_win": actual_home_win}
 
    def get_accuracy_report(self) -> Dict[str, Any]:
        """Aggregate accuracy across all evaluated predictions."""
        total = self.db.query(Prediction).count()
        evaluated = self.db.query(Prediction).filter(Prediction.brier_score.isnot(None)).all()
        if not evaluated:
            return {"total_predictions": total, "evaluated_predictions": 0,
                    "avg_brier_score": None, "hit_rate": None}
 
        avg_brier = sum(p.brier_score for p in evaluated) / len(evaluated)
        hits = sum(
            1 for p in evaluated
            if (p.home_win_probability >= 0.5) == bool(p.actual_home_win)
        )
        return {
            "total_predictions": total,
            "evaluated_predictions": len(evaluated),
            "avg_brier_score": round(avg_brier, 4),
            "hit_rate": round(hits / len(evaluated), 4),
        }