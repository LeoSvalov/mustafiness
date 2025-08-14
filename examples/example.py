#!/usr/bin/env python3
"""
Example script demonstrating how to use Mustafiness.

This script shows various ways to collect and analyze Fantasy Premier League data.
"""

import asyncio
import logging
from pathlib import Path

from src.collector import FPLDataCollector, collect_fpl_data
from src.models import Position


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main():
    """Main function demonstrating Mustafiness data collection and analysis."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Mustafiness Data Collection Example")
    
    # Method 1: Using the convenience function
    logger.info("Method 1: Using convenience function")
    collector = await collect_fpl_data(force_refresh=False, export_format="csv")
    
    # Method 2: Using the collector class directly
    logger.info("Method 2: Using collector class directly")
    collector2 = FPLDataCollector(use_async=True, cache_data=True)
    fpl_data = await collector2.collect_all_data(force_refresh=False)
    
    # Get summary statistics
    stats = collector.get_summary_stats()
    logger.info(f"Summary Statistics: {stats}")
    
    # Get current gameweek
    current_gw = collector.get_current_gameweek()
    if current_gw:
        logger.info(f"Current Gameweek: {current_gw.name} (ID: {current_gw.id})")
    
    # Get next gameweek
    next_gw = collector.get_next_gameweek()
    if next_gw:
        logger.info(f"Next Gameweek: {next_gw.name} (ID: {next_gw.id})")
    
    # Get players by position
    goalkeepers = collector.get_players(position="GK")
    defenders = collector.get_players(position="DEF")
    midfielders = collector.get_players(position="MID")
    forwards = collector.get_players(position="FWD")
    
    logger.info(f"Players by position:")
    logger.info(f"  Goalkeepers: {len(goalkeepers)}")
    logger.info(f"  Defenders: {len(defenders)}")
    logger.info(f"  Midfielders: {len(midfielders)}")
    logger.info(f"  Forwards: {len(forwards)}")
    
    # Get teams
    teams = collector.get_teams()
    logger.info(f"Total teams: {len(teams)}")
    
    # Get fixtures for next gameweek
    if next_gw:
        next_fixtures = collector.get_fixtures(gameweek=next_gw.id)
        logger.info(f"Fixtures for {next_gw.name}: {len(next_fixtures)}")
        
        for fixture in next_fixtures[:3]:  # Show first 3 fixtures
            logger.info(f"  {fixture.team_h_name} vs {fixture.team_a_name} (Difficulty: {fixture.difficulty})")
    
    # Use the data processor for analysis
    processor = collector.processor
    
    # Get top performers
    top_performers = processor.get_top_performers(top_n=5)
    logger.info("Top 5 performers:")
    for _, player in top_performers.iterrows():
        logger.info(f"  {player['name']} ({player['team_name']}) - {player['total_points']} points")
    
    # Get value players
    value_players = processor.get_value_players(top_n=5)
    logger.info("Top 5 value players:")
    for _, player in value_players.iterrows():
        logger.info(f"  {player['name']} ({player['team_name']}) - {player['points_per_million']:.2f} pts/million")
    
    # Get form players
    form_players = processor.get_form_players(min_form=6.0, top_n=5)
    logger.info("Top 5 form players (form >= 6.0):")
    for _, player in form_players.iterrows():
        logger.info(f"  {player['name']} ({player['team_name']}) - Form: {player['form']:.1f}")
    
    # Get transfer targets
    transfer_targets = processor.get_transfer_targets(min_transfers_in=5000, top_n=5)
    logger.info("Top 5 transfer targets:")
    for _, player in transfer_targets.iterrows():
        logger.info(f"  {player['name']} ({player['team_name']}) - Net transfers: {player['transfer_balance']}")
    
    # Get differential players
    differentials = processor.get_differential_players(max_selection=3.0, min_points=50, top_n=5)
    logger.info("Top 5 differential players (ownership <= 3%):")
    for _, player in differentials.iterrows():
        logger.info(f"  {player['name']} ({player['team_name']}) - Ownership: {player['selected_by_percent']}%")
    
    # Get injury concerns
    injuries = processor.get_injury_concerns()
    if not injuries.empty:
        logger.info("Players with injury concerns:")
        for _, player in injuries.head(5).iterrows():
            logger.info(f"  {player['name']} ({player['team_name']}) - Status: {player['status']}, News: {player['news']}")
    
    # Get expected points analysis
    expected_points = processor.get_expected_points_analysis()
    if not expected_points.empty:
        logger.info("Top 5 players by expected points:")
        for _, player in expected_points.head(5).iterrows():
            logger.info(f"  {player['name']} ({player['team_name']}) - Expected: {player['ep_this']}")
    
    # Get fixture difficulty analysis
    fixture_analysis = processor.get_fixture_difficulty_analysis()
    logger.info("Fixture difficulty analysis (next 5 gameweeks):")
    for _, fixture in fixture_analysis.head(10).iterrows():
        logger.info(f"  GW{fixture['gameweek']}: {fixture['team_name']} vs {fixture['opponent_name']} (Difficulty: {fixture['difficulty']})")
    
    # Get team analysis
    team_analysis = processor.get_team_analysis()
    logger.info("Team analysis (top 5 by points):")
    top_teams = team_analysis.nlargest(5, 'points')
    for _, team in top_teams.iterrows():
        logger.info(f"  {team['team_name']} - Points: {team['points']}, Goals: {team['goals_for']}-{team['goals_against']}")
    
    # Get position analysis
    position_analysis = processor.get_position_analysis()
    logger.info("Position analysis:")
    for position, stats in position_analysis.items():
        logger.info(f"  {position}: {stats['count']} players, avg points: {stats['avg_points']:.1f}, avg price: {stats['avg_price']:.1f}")
    
    # Export data to different formats
    logger.info("Exporting data...")
    collector.export_data(format="csv")
    collector.export_data(format="json")
    
    logger.info("Example completed successfully!")
    
    return collector


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
