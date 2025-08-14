"""
Main FPL data collector that orchestrates data collection and processing.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .api_client import FPLAPIClient, FPLAPIClientSync
from .data_processor import FPLDataProcessor
from .models import FPLData, Player, Team, Fixture, Gameweek
from .config import config
from .exceptions import FPLException, APIError, DataProcessingError


class FPLDataCollector:
    """Main FPL data collector with comprehensive data gathering capabilities."""
    
    def __init__(self, use_async: bool = True, cache_data: bool = True):
        """Initialize the FPL data collector.
        
        Args:
            use_async: Whether to use async API client (default: True)
            cache_data: Whether to cache data locally (default: True)
        """
        self.use_async = use_async
        self.cache_data = cache_data
        self.logger = logging.getLogger(__name__)
        
        # Initialize API client
        if use_async:
            self.api_client = None  # Will be initialized in async context
        else:
            self.api_client = FPLAPIClientSync()
        
        # Data storage
        self.fpl_data: Optional[FPLData] = None
        self.processor: Optional[FPLDataProcessor] = None
        
        # Cache file paths
        self.cache_dir = config.data.CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.bootstrap_cache_file = self.cache_dir / "bootstrap_static.json"
        self.players_cache_dir = self.cache_dir / "players"
        self.players_cache_dir.mkdir(exist_ok=True)
    
    async def collect_all_data(self, force_refresh: bool = False) -> FPLData:
        """Collect all FPL data including bootstrap static and individual player data.
        
        Args:
            force_refresh: Whether to force refresh cached data
            
        Returns:
            Complete FPL data
        """
        self.logger.info("Starting FPL data collection...")
        
        # Collect bootstrap static data
        self.fpl_data = await self._collect_bootstrap_static(force_refresh)
        
        # Collect individual player data
        await self._collect_player_details(force_refresh)
        
        # Initialize data processor
        self.processor = FPLDataProcessor(self.fpl_data)
        
        self.logger.info(f"Data collection completed. Collected data for {len(self.fpl_data.players)} players.")
        return self.fpl_data
    
    async def _collect_bootstrap_static(self, force_refresh: bool = False) -> FPLData:
        """Collect bootstrap static data."""
        # Check cache first
        if not force_refresh and self.bootstrap_cache_file.exists():
            try:
                self.logger.info("Loading bootstrap data from cache...")
                with open(self.bootstrap_cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is recent (less than 1 hour old)
                cache_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01'))
                if (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour
                    self.logger.info("Using cached bootstrap data")
                    return FPLData(**cached_data['data'])
                else:
                    self.logger.info("Cache is stale, refreshing data...")
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")
        
        # Fetch fresh data
        self.logger.info("Fetching fresh bootstrap data...")
        async with FPLAPIClient() as client:
            fpl_data = await client.get_bootstrap_static()
        
        # Cache the data
        if self.cache_data:
            try:
                cache_data = {
                    'cached_at': datetime.now().isoformat(),
                    'data': fpl_data.dict()
                }
                with open(self.bootstrap_cache_file, 'w') as f:
                    json.dump(cache_data, f, default=str)
                self.logger.info("Bootstrap data cached successfully")
            except Exception as e:
                self.logger.warning(f"Failed to cache bootstrap data: {e}")
        
        return fpl_data
    
    async def _collect_player_details(self, force_refresh: bool = False):
        """Collect detailed data for each player."""
        if not self.fpl_data:
            raise DataProcessingError("Bootstrap data must be collected first")
        
        self.logger.info(f"Collecting detailed data for {len(self.fpl_data.players)} players...")
        
        # Collect player details in batches to avoid overwhelming the API
        batch_size = 10
        total_players = len(self.fpl_data.players)
        
        async with FPLAPIClient() as client:
            for i in range(0, total_players, batch_size):
                batch = self.fpl_data.players[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}/{(total_players + batch_size - 1)//batch_size}")
                
                # Process batch concurrently
                tasks = []
                for player in batch:
                    task = self._collect_player_detail(client, player, force_refresh)
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Small delay between batches to be respectful to the API
                await asyncio.sleep(0.5)
    
    async def _collect_player_detail(self, client: FPLAPIClient, player: Player, force_refresh: bool = False):
        """Collect detailed data for a single player."""
        cache_file = self.players_cache_dir / f"player_{player.id}.json"
        
        # Check cache first
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is recent (less than 6 hours old for player data)
                cache_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01'))
                if (datetime.now() - cache_time).total_seconds() < 21600:  # 6 hours
                    return
            except Exception:
                pass
        
        try:
            # Fetch player detail
            player_detail = await client.get_player_summary(player.id)
            
            # Cache the data
            if self.cache_data:
                try:
                    cache_data = {
                        'cached_at': datetime.now().isoformat(),
                        'data': player_detail
                    }
                    with open(cache_file, 'w') as f:
                        json.dump(cache_data, f, default=str)
                except Exception as e:
                    self.logger.warning(f"Failed to cache player {player.id} data: {e}")
        
        except Exception as e:
            self.logger.warning(f"Failed to collect data for player {player.id}: {e}")
    
    def get_players(self, position: Optional[str] = None, team_id: Optional[int] = None) -> List[Player]:
        """Get players with optional filtering."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        players = self.fpl_data.players
        
        if position:
            players = [p for p in players if p.position.value == position.upper()]
        
        if team_id:
            players = [p for p in players if p.team == team_id]
        
        return players
    
    def get_teams(self) -> List[Team]:
        """Get all teams."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        return self.fpl_data.teams
    
    def get_fixtures(self, gameweek: Optional[int] = None) -> List[Fixture]:
        """Get fixtures with optional gameweek filtering."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        fixtures = self.fpl_data.fixtures
        
        if gameweek:
            fixtures = [f for f in fixtures if f.event == gameweek]
        
        return fixtures
    
    def get_gameweeks(self) -> List[Gameweek]:
        """Get all gameweeks."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        return self.fpl_data.gameweeks
    
    def get_current_gameweek(self) -> Optional[Gameweek]:
        """Get the current gameweek."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        return self.fpl_data.current_gameweek
    
    def get_next_gameweek(self) -> Optional[Gameweek]:
        """Get the next gameweek."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        return self.fpl_data.next_gameweek
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        return next((team for team in self.fpl_data.teams if team.id == team_id), None)
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Get player by ID."""
        if not self.fpl_data:
            raise DataProcessingError("No data available. Call collect_all_data() first.")
        
        return next((player for player in self.fpl_data.players if player.id == player_id), None)
    
    def export_data(self, format: str = "csv", output_dir: Optional[Path] = None):
        """Export processed data to various formats."""
        if not self.processor:
            raise DataProcessingError("No processor available. Call collect_all_data() first.")
        
        if output_dir is None:
            output_dir = config.data.EXPORT_DIR
        
        output_dir.mkdir(exist_ok=True)
        
        if format.lower() == "csv":
            self._export_to_csv(output_dir)
        elif format.lower() == "json":
            self._export_to_json(output_dir)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_to_csv(self, output_dir: Path):
        """Export data to CSV files."""
        self.logger.info("Exporting data to CSV files...")
        
        # Export main dataframes
        self.processor.players_df.to_csv(output_dir / "players.csv", index=False)
        self.processor.teams_df.to_csv(output_dir / "teams.csv", index=False)
        self.processor.fixtures_df.to_csv(output_dir / "fixtures.csv", index=False)
        
        # Export analysis data
        self.processor.get_team_analysis().to_csv(output_dir / "team_analysis.csv", index=False)
        self.processor.get_fixture_difficulty_analysis().to_csv(output_dir / "fixture_analysis.csv", index=False)
        
        # Export position-specific data
        for position in ["GK", "DEF", "MID", "FWD"]:
            pos_players = self.processor.get_players_by_position(position)
            pos_players.to_csv(output_dir / f"players_{position.lower()}.csv", index=False)
        
        # Export top performers
        self.processor.get_top_performers().to_csv(output_dir / "top_performers.csv", index=False)
        self.processor.get_value_players().to_csv(output_dir / "value_players.csv", index=False)
        self.processor.get_form_players().to_csv(output_dir / "form_players.csv", index=False)
        
        # Export transfer targets and differentials
        self.processor.get_transfer_targets().to_csv(output_dir / "transfer_targets.csv", index=False)
        self.processor.get_differential_players().to_csv(output_dir / "differential_players.csv", index=False)
        
        # Export injury concerns
        self.processor.get_injury_concerns().to_csv(output_dir / "injury_concerns.csv", index=False)
        
        # Export expected points
        self.processor.get_expected_points_analysis().to_csv(output_dir / "expected_points.csv", index=False)
        
        self.logger.info(f"Data exported to {output_dir}")
    
    def _export_to_json(self, output_dir: Path):
        """Export data to JSON files."""
        self.logger.info("Exporting data to JSON files...")
        
        # Export main data
        with open(output_dir / "players.json", 'w') as f:
            json.dump([p.dict() for p in self.fpl_data.players], f, default=str, indent=2)
        
        with open(output_dir / "teams.json", 'w') as f:
            json.dump([t.dict() for t in self.fpl_data.teams], f, default=str, indent=2)
        
        with open(output_dir / "fixtures.json", 'w') as f:
            json.dump([f.dict() for f in self.fpl_data.fixtures], f, default=str, indent=2)
        
        with open(output_dir / "gameweeks.json", 'w') as f:
            json.dump([g.dict() for g in self.fpl_data.gameweeks], f, default=str, indent=2)
        
        # Export summary stats
        with open(output_dir / "summary_stats.json", 'w') as f:
            json.dump(self.processor.get_summary_stats(), f, default=str, indent=2)
        
        self.logger.info(f"Data exported to {output_dir}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.processor:
            raise DataProcessingError("No processor available. Call collect_all_data() first.")
        
        return self.processor.get_summary_stats()
    
    def clear_cache(self):
        """Clear all cached data."""
        self.logger.info("Clearing cache...")
        
        if self.bootstrap_cache_file.exists():
            self.bootstrap_cache_file.unlink()
        
        for cache_file in self.players_cache_dir.glob("*.json"):
            cache_file.unlink()
        
        self.logger.info("Cache cleared successfully")


# Convenience functions for easy usage
async def collect_fpl_data(force_refresh: bool = False, export_format: str = "csv") -> FPLDataCollector:
    """Convenience function to collect FPL data.
    
    Args:
        force_refresh: Whether to force refresh cached data
        export_format: Format to export data (csv, json, or none)
        
    Returns:
        FPLDataCollector instance with collected data
    """
    collector = FPLDataCollector()
    await collector.collect_all_data(force_refresh=force_refresh)
    
    if export_format:
        collector.export_data(format=export_format)
    
    return collector


def collect_fpl_data_sync(force_refresh: bool = False, export_format: str = "csv") -> FPLDataCollector:
    """Synchronous version of collect_fpl_data."""
    collector = FPLDataCollector(use_async=False)
    
    # For sync version, we need to run the async function in an event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(collector.collect_all_data(force_refresh=force_refresh))
        
        if export_format:
            collector.export_data(format=export_format)
        
        return collector
    finally:
        loop.close()
