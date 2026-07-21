"""
SQLAlchemy models and migration for the NBA Predictor.
 
Persists teams, stored game predictions, and post-game evaluation (Brier score)
so prediction accuracy can be tracked over time.
"""
 
import os
from datetime import datetime
 
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
 
DATABASE_URL = os.getenv("NBA_DATABASE_URL", "sqlite:///nba_predictor.db")
 
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
Base = declarative_base()
 
 
class Team(Base):
    __tablename__ = "teams"
 
    id = Column(String(8), primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    conference = Column(String(8), nullable=False)
    division = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
 
 
class Game(Base):
    __tablename__ = "games"
 
    id = Column(Integer, primary_key=True, index=True)
    home_id = Column(String(8), nullable=False, index=True)
    away_id = Column(String(8), nullable=False, index=True)
    season = Column(Integer, nullable=False, index=True)
    game_date = Column(String(16), nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
 
    predictions = relationship("Prediction", back_populates="game", cascade="all, delete-orphan")
 
 
class Prediction(Base):
    __tablename__ = "predictions"
 
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    home_win_probability = Column(Float, nullable=False)
    projected_home_score = Column(Float, nullable=False)
    projected_away_score = Column(Float, nullable=False)
    expected_margin = Column(Float, nullable=False)
    model_version = Column(String(16), nullable=False)
    actual_home_win = Column(Boolean, nullable=True)
    brier_score = Column(Float, nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
 
    game = relationship("Game", back_populates="predictions")
 
 
def create_database() -> None:
    """Create all tables."""
    Base.metadata.create_all(engine)
 
 
def migrate_from_static(season: int = 2026) -> None:
    """Create the DB and load team + completed-game metadata from static modules."""
    from data.season_results import SEASON, get_completed_games
    from data.team_data import get_all_teams
 
    create_database()
    db = SessionLocal()
    try:
        existing_teams = {t.id for t in db.query(Team).all()}
        for team in get_all_teams():
            if team["id"] not in existing_teams:
                db.add(Team(
                    id=team["id"],
                    name=team["name"],
                    conference=team["conference"],
                    division=team.get("division"),
                ))
 
        existing_games = {
            (g.home_id, g.away_id, g.game_date) for g in db.query(Game).all()
        }
        for g in get_completed_games():
            key = (g["home"], g["away"], g["date"])
            if key not in existing_games:
                db.add(Game(
                    home_id=g["home"],
                    away_id=g["away"],
                    season=SEASON,
                    game_date=g["date"],
                    completed=True,
                    home_score=g["home_score"],
                    away_score=g["away_score"],
                ))
        db.commit()
    finally:
        db.close()