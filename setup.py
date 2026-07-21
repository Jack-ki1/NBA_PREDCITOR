#!/usr/bin/env python
"""
Setup script for NBA Predictor.

This script initializes the database and syncs the latest data.
"""

import os
import sys
import subprocess

def setup_database():
    """Initialize the database with initial data"""
    print("Initializing database...")
    try:
        from database.models import migrate_from_static
        migrate_from_static()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False
    return True

def sync_data():
    """Sync with latest NBA data"""
    print("Syncing with latest NBA data...")
    try:
        from data.synchronizer import update_local_data
        data = update_local_data()
        print(f"✓ Synced {len(data['games'])} games and {len(data['team_stats'])} teams")
    except Exception as e:
        print(f"⚠ Warning: Could not sync live data (using static data): {e}")
        # This is okay - we can proceed with static data
    return True

def main():
    """Main setup function"""
    print("🚀 NBA Predictor Setup")
    print("=" * 50)
    
    # Initialize database
    if not setup_database():
        print("❌ Database setup failed. Exiting.")
        sys.exit(1)
    
    # Sync data
    sync_data()
    
    print("\n✅ Setup completed successfully!")
    print("\nTo launch the dashboard:")
    print("  python main.py dashboard")
    print("\nTo run from command line:")
    print("  python main.py predict --home BOS --away NYK")

if __name__ == "__main__":
    main()