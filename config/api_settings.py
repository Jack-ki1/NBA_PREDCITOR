"""
API settings and configuration for external data sources.

This module handles configuration for various NBA data APIs and external services.
"""

import os
from typing import Optional
from pydantic import BaseModel


class APISettings(BaseModel):
    """Settings for various API integrations"""
    
    # NBA API settings (these are public endpoints, no key needed)
    nba_api_enabled: bool = True
    nba_api_timeout: int = 30  # seconds
    nba_api_retry_attempts: int = 3
    
    # SportsData.IO API (optional paid service)
    sportsdata_api_key: Optional[str] = os.getenv("SPORTSDATA_API_KEY")
    sportsdata_enabled: bool = bool(sportsdata_api_key)
    
    # Basketball Reference scraper settings
    basketball_reference_enabled: bool = True
    basketball_reference_user_agent: str = "Mozilla/5.0 (compatible; NBA-Predictor/1.0)"
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 10
    rate_limit_sleep_time: float = 6.0  # seconds between requests
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_hours: int = 2
    cache_directory: str = "data/cache"


# Create a singleton instance
api_settings = APISettings()


def get_api_settings() -> APISettings:
    """Get the API settings instance"""
    return api_settings


# For backward compatibility
NBA_API_ENABLED = api_settings.nba_api_enabled
SPORTSDATA_ENABLED = api_settings.sportsdata_enabled
RATE_LIMIT_REQUESTS_PER_MINUTE = api_settings.rate_limit_requests_per_minute