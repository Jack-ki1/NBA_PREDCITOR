"""
Data synchronizer for keeping NBA predictor data up to date.

This module handles regular synchronization of team stats, game results,
and other data from various sources to ensure the prediction engine
has the most current information.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from .api_client import NBAApiClient


class DataSynchronizer:
    """
    Handles synchronization of data from external sources to local storage
    """
    
    def __init__(self, data_dir: str = "data/cache"):
        self.data_dir = data_dir
        self.client = NBAApiClient()
        self.ensure_cache_dir()
        
    def ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_cache_file_path(self, data_type: str) -> str:
        """Get the file path for cached data of a specific type"""
        return os.path.join(self.data_dir, f"{data_type}_cache.json")
    
    def is_cache_valid(self, data_type: str, hours: int = 1) -> bool:
        """Check if cached data is still valid based on age"""
        cache_file = self.get_cache_file_path(data_type)
        if not os.path.exists(cache_file):
            return False
        
        mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return datetime.now() - mod_time < timedelta(hours=hours)
    
    def load_cached_data(self, data_type: str) -> Any:
        """Load cached data from file"""
        cache_file = self.get_cache_file_path(data_type)
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None
    
    def save_cached_data(self, data_type: str, data: Any):
        """Save data to cache file"""
        cache_file = self.get_cache_file_path(data_type)
        with open(cache_file, 'w') as f:
            json.dump(data, f, default=str, indent=2)
    
    def sync_games(self, force_update: bool = False) -> List[Dict[str, Any]]:
        """Sync game results from API"""
        data_type = "games"
        
        if not force_update and self.is_cache_valid(data_type, hours=2):
            cached_data = self.load_cached_data(data_type)
            if cached_data:
                print(f"Loaded {len(cached_data)} games from cache")
                return cached_data
        
        print("Fetching latest game results...")
        games = self.client.get_current_season_games()
        self.save_cached_data(data_type, games)
        print(f"Fetched and cached {len(games)} games")
        return games
    
    def sync_team_stats(self, force_update: bool = False) -> Dict[str, Any]:
        """Sync team stats from API"""
        data_type = "team_stats"
        
        if not force_update and self.is_cache_valid(data_type, hours=4):
            cached_data = self.load_cached_data(data_type)
            if cached_data:
                print(f"Loaded team stats for {len(cached_data)} teams from cache")
                return cached_data
        
        print("Fetching latest team statistics...")
        team_stats = self.client.get_all_teams_current_stats()
        self.save_cached_data(data_type, team_stats)
        print(f"Fetched and cached stats for {len(team_stats)} teams")
        return team_stats
    
    def sync_all_data(self, force_update: bool = False) -> Dict[str, Any]:
        """Sync all data types"""
        print("Starting data synchronization...")
        
        games = self.sync_games(force_update)
        team_stats = self.sync_team_stats(force_update)
        
        result = {
            'games': games,
            'team_stats': team_stats,
            'sync_timestamp': datetime.now().isoformat()
        }
        
        # Save overall sync status
        self.save_cached_data("full_sync", result)
        
        print(f"Synchronization complete: {len(games)} games, {len(team_stats)} teams")
        return result
    
    def get_fresh_data(self) -> Dict[str, Any]:
        """Get the most recent synchronized data"""
        cached_data = self.load_cached_data("full_sync")
        if cached_data and not self.is_cache_valid("full_sync", hours=2):
            # Refresh if cache is old
            return self.sync_all_data(force_update=True)
        elif cached_data:
            return cached_data
        else:
            # Initial sync if no cache exists
            return self.sync_all_data()


def update_local_data():
    """
    Convenience function to update local data files with fresh API data
    """
    synchronizer = DataSynchronizer()
    return synchronizer.get_fresh_data()


def background_sync(interval_minutes: int = 60):
    """
    Run continuous background synchronization
    
    Args:
        interval_minutes: How often to sync data in minutes
    """
    synchronizer = DataSynchronizer()
    
    print(f"Starting background sync (every {interval_minutes} minutes)")
    while True:
        try:
            synchronizer.sync_all_data(force_update=True)
            print(f"Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("Background sync stopped by user")
            break
        except Exception as e:
            print(f"Error during sync: {e}")
            # Wait a shorter time if there was an error
            time.sleep(10 * 60)  # Wait 10 minutes before retrying


if __name__ == "__main__":
    # Example usage
    sync = DataSynchronizer()
    data = sync.get_fresh_data()
    print(f"Synced data includes {len(data['games'])} games and {len(data['team_stats'])} teams")