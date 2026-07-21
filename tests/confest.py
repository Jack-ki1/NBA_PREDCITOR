"""Pytest configuration: make the nba_predictor package root importable."""
 
import os
import sys
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))