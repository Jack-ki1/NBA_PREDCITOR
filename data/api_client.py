"""
NBA API client for fetching live data.

This module integrates with the nba_api library to fetch current season data,
including team stats, player stats, and game results to keep the predictor
up to date with the latest information.
"""

import time
from typing import Dict, List, Optional
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, teamgamelog, commonteamroster
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamestimatedmetrics
import requests


class NBAApiClient:
    """
    Client for fetching NBA data from various sources including the official NBA API
    """
    
    def __init__(self):
        # Map team abbreviations to NBA API team IDs
        self.team_mapping = {}
        all_teams = teams.get_teams()
        for team in all_teams:
            self.team_mapping[team['abbreviation'].upper()] = team['id']
        
        # Reverse mapping for getting abbreviations from IDs
        self.id_to_abbr = {v: k for k, v in self.team_mapping.items()}
    
    def get_current_season_games(self, season_year: str = "2024-25") -> List[Dict]:
        """
        Fetch all games for the current season
        
        Args:
            season_year: Format like "2024-25"
            
        Returns:
            List of game dictionaries with date, home, away, scores
        """
        try:
            # Get all games for the current season
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_year,
                season_type_nullable='Regular Season'
            )
            games_df = gamefinder.get_data_frames()[0]
            
            # Filter for completed games only (both teams have scores)
            completed_games = games_df[
                (games_df['WL'].notna()) & 
                (games_df['PTS'].notna())
            ].copy()
            
            # Process games to match our expected format
            processed_games = []
            processed_game_ids = set()
            
            for _, game in completed_games.iterrows():
                # Create a unique identifier for the game
                game_id = f"{game['GAME_ID']}_{game['TEAM_ABBREVIATION']}"
                
                if game_id in processed_game_ids:
                    continue
                    
                processed_game_ids.add(game_id)
                
                # Find opponent info for the same game
                opponent_games = completed_games[
                    (completed_games['GAME_ID'] == game['GAME_ID']) &
                    (completed_games['TEAM_ABBREVIATION'] != game['TEAM_ABBREVIATION'])
                ]
                
                if not opponent_games.empty:
                    opponent = opponent_games.iloc[0]
                    
                    # Determine home/away based on location or other indicators
                    # In the API, we typically need to determine this based on matchup string
                    matchup = game['MATCHUP']
                    is_home = 'vs' in matchup
                    home_abbr = game['TEAM_ABBREVIATION'] if is_home else opponent['TEAM_ABBREVIATION']
                    away_abbr = opponent['TEAM_ABBREVIATION'] if is_home else game['TEAM_ABBREVIATION']
                    
                    home_score = game['PTS'] if is_home else opponent['PTS']
                    away_score = opponent['PTS'] if is_home else game['PTS']
                    
                    processed_games.append({
                        'date': game['GAME_DATE'],
                        'home': home_abbr.upper(),
                        'away': away_abbr.upper(),
                        'home_score': int(home_score),
                        'away_score': int(away_score)
                    })
                    
                    # Add the paired game to prevent duplication
                    paired_game_id = f"{game['GAME_ID']}_{opponent['TEAM_ABBREVIATION']}"
                    processed_game_ids.add(paired_game_id)
            
            return processed_games
            
        except Exception as e:
            print(f"Error fetching season games: {e}")
            # Return empty list if API fails
            return []
    
    def get_team_stats(self, team_abbr: str, season_year: str = "2024-25") -> Dict:
        """
        Fetch current season team statistics
        
        Args:
            team_abbr: Team abbreviation (e.g., 'LAL')
            season_year: Format like "2024-25"
            
        Returns:
            Dictionary with team stats
        """
        try:
            team_id = self.team_mapping.get(team_abbr.upper())
            if not team_id:
                return {}

            # Get team game logs to calculate season averages
            try:
                # Try with the correct parameter name
                gamelog = teamgamelog.TeamGameLog(
                    team_id=team_id,
                    season=season_year,
                    season_type_all_star='Regular Season'  # Correct parameter name
                )
            except TypeError:
                # Fallback to the old parameter name if needed
                gamelog = teamgamelog.TeamGameLog(
                    team_id=team_id,
                    season=season_year,
                    season_type_nullable='Regular Season'
                )
            
            gamelog_df = gamelog.get_data_frames()[0]
            
            if gamelog_df.empty:
                return {}
            
            # Check if 'PLUS_MINUS' column exists, otherwise use a default
            if 'PLUS_MINUS' in gamelog_df.columns:
                avg_plus_minus = gamelog_df['PLUS_MINUS'].mean()
                recent_form = gamelog_df['PLUS_MINUS'].head(10).tolist()
            else:
                # If PLUS_MINUS doesn't exist, calculate from PTS and OPP_PTS if available
                if 'PTS' in gamelog_df.columns and 'OPP_PTS' in gamelog_df.columns and len(gamelog_df) > 1:
                    # Calculate average point differential differently
                    point_diffs = gamelog_df['PTS'] - gamelog_df['OPP_PTS']
                    avg_plus_minus = point_diffs.mean()
                    recent_form = point_diffs.head(10).tolist()
                else:
                    avg_plus_minus = 0.0
                    recent_form = [0.0] * min(10, len(gamelog_df))
            
            # Basic stats calculation with fallback values
            avg_points = gamelog_df['PTS'].mean() if 'PTS' in gamelog_df.columns else 110.0
            avg_opp_points = gamelog_df['OPP_PTS'].mean() if 'OPP_PTS' in gamelog_df.columns else 110.0
            
            # If we have plus-minus, use it to adjust opponent points
            if 'PLUS_MINUS' in gamelog_df.columns or 'OPP_PTS' in gamelog_df.columns:
                avg_opp_points = avg_points - avg_plus_minus  # Since plus_minus = team - opponent
            
            avg_pace = 98.5  # Default pace if not available
            
            return {
                'off_rating': avg_points,  # Simplified approximation
                'def_rating': avg_opp_points,  # Simplified approximation
                'pace': avg_pace,
                'recent_form': recent_form
            }
        except Exception as e:
            print(f"Error fetching team stats for {team_abbr}: {e}")
            # Return default stats if there's an error
            return {
                'off_rating': 110.0,
                'def_rating': 110.0,
                'pace': 98.5,
                'recent_form': [0.0] * 10
            }
    
    def get_all_teams_current_stats(self, season_year: str = "2024-25") -> Dict:
        """
        Fetch current stats for all NBA teams
        """
        all_stats = {}
        for abbr in self.team_mapping.keys():
            stats = self.get_team_stats(abbr, season_year)
            if stats:
                all_stats[abbr] = stats
        return all_stats
    
    def get_latest_season_year(self) -> str:
        """
        Determine the current NBA season year
        """
        import datetime
        current_date = datetime.date.today()
        # NBA season typically runs from October to April
        if current_date.month >= 10:
            return f"{current_date.year}-{str(current_date.year + 1)[-2:]}"
        else:
            return f"{current_date.year - 1}-{str(current_date.year)[-2:]}"


def sync_with_live_data():
    """
    Synchronize the local data with live NBA data
    """
    client = NBAApiClient()
    current_season = client.get_latest_season_year()
    
    print(f"Fetching data for season: {current_season}")
    
    # Get latest games
    games = client.get_current_season_games(current_season)
    print(f"Fetched {len(games)} completed games")
    
    # Get latest team stats
    team_stats = client.get_all_teams_current_stats(current_season)
    print(f"Fetched stats for {len(team_stats)} teams")
    
    return {
        'games': games,
        'team_stats': team_stats,
        'season': current_season
    }


if __name__ == "__main__":
    # Test the API client
    sync_with_live_data()