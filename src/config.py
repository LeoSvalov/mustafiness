"""
Configuration management for the FPL Data Collector.
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    """API configuration settings."""
    
    # Base URLs
    BOOTSTRAP_STATIC_URL: str = "https://fantasy.premierleague.com/api/bootstrap-static/"
    ELEMENT_SUMMARY_URL: str = "https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    ENTRY_URL: str = "https://fantasy.premierleague.com/api/entry/{entry_id}/"
    ENTRY_HISTORY_URL: str = "https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
    ENTRY_GW_URL: str = "https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/"
    ENTRY_TRANSFERS_URL: str = "https://fantasy.premierleague.com/api/entry/{entry_id}/transfers/"
    FIXTURES_URL: str = "https://fantasy.premierleague.com/api/fixtures/"
    
    # Request settings
    TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    RATE_LIMIT_DELAY: float = 0.1  # 100ms between requests
    
    # Headers
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class DataConfig:
    """Data storage and processing configuration."""
    
    # Data directories
    DATA_DIR: Path = Path("data")
    CACHE_DIR: Path = Path("cache")
    EXPORT_DIR: Path = Path("exports")
    
    # File formats
    DEFAULT_FORMAT: str = "csv"
    SUPPORTED_FORMATS: tuple = ("csv", "json", "parquet")
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        self.DATA_DIR.mkdir(exist_ok=True)
        self.CACHE_DIR.mkdir(exist_ok=True)
        self.EXPORT_DIR.mkdir(exist_ok=True)


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    LEVEL: str = "INFO"
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE: Optional[Path] = None


class Config:
    """Main configuration class that combines all config sections."""
    
    def __init__(self):
        self.api = APIConfig()
        self.data = DataConfig()
        self.logging = LoggingConfig()
        
        # Load environment variables
        self._load_env_vars()
    
    def _load_env_vars(self):
        """Load configuration from environment variables."""
        # API settings
        if timeout := os.getenv("FPL_API_TIMEOUT"):
            self.api.TIMEOUT = int(timeout)
        
        if max_retries := os.getenv("FPL_MAX_RETRIES"):
            self.api.MAX_RETRIES = int(max_retries)
        
        # Data settings
        if data_dir := os.getenv("FPL_DATA_DIR"):
            self.data.DATA_DIR = Path(data_dir)
        
        if database_url := os.getenv("FPL_DATABASE_URL"):
            self.data.DATABASE_URL = database_url
        
        # Logging settings
        if log_level := os.getenv("FPL_LOG_LEVEL"):
            self.logging.LEVEL = log_level
        
        if log_file := os.getenv("FPL_LOG_FILE"):
            self.logging.FILE = Path(log_file)


# Global configuration instance
config = Config()
