#!/usr/bin/env python3
"""
Command-line interface for the FPL Data Collector.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from src.collector import FPLDataCollector, collect_fpl_data
from src.models import Position


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def collect_data(args):
    """Collect FPL data."""
    print("Collecting FPL data...")
    
    try:
        collector = await collect_fpl_data(
            force_refresh=args.force_refresh,
            export_format=args.format if args.export else None
        )
        
        # Print summary
        stats = collector.get_summary_stats()
        print(f"\nData collection completed!")
        print(f"Total players: {stats['total_players']}")
        print(f"Total teams: {stats['total_teams']}")
        print(f"Total fixtures: {stats['total_fixtures']}")
        print(f"Current gameweek: {stats['current_gameweek']}")
        print(f"Next gameweek: {stats['next_gameweek']}")
        
        if args.export:
            print(f"Data exported to {args.output_dir}")
        
        return collector
    
    except Exception as e:
        print(f"Error collecting data: {e}")
        return None


async def analyze_players(args):
    """Analyze players."""
    print("Analyzing players...")
    
    collector = FPLDataCollector()
    await collector.collect_all_data(force_refresh=args.force_refresh)
    processor = collector.processor
    
    if args.analysis == "top":
        players = processor.get_top_performers(top_n=args.limit)
        print(f"\nTop {args.limit} performers:")
        for _, player in players.iterrows():
            print(f"  {player['name']} ({player['team_name']}) - {player['total_points']} points")
    
    elif args.analysis == "value":
        players = processor.get_value_players(min_points=args.min_points, top_n=args.limit)
        print(f"\nTop {args.limit} value players (min {args.min_points} points):")
        for _, player in players.iterrows():
            print(f"  {player['name']} ({player['team_name']}) - {player['points_per_million']:.2f} pts/million")
    
    elif args.analysis == "form":
        players = processor.get_form_players(min_form=args.min_form, top_n=args.limit)
        print(f"\nTop {args.limit} form players (min form {args.min_form}):")
        for _, player in players.iterrows():
            print(f"  {player['name']} ({player['team_name']}) - Form: {player['form']:.1f}")
    
    elif args.analysis == "transfers":
        players = processor.get_transfer_targets(min_transfers_in=args.min_transfers, top_n=args.limit)
        print(f"\nTop {args.limit} transfer targets (min {args.min_transfers} transfers in):")
        for _, player in players.iterrows():
            print(f"  {player['name']} ({player['team_name']}) - Net transfers: {player['transfer_balance']}")
    
    elif args.analysis == "differentials":
        players = processor.get_differential_players(
            max_selection=args.max_ownership, 
            min_points=args.min_points, 
            top_n=args.limit
        )
        print(f"\nTop {args.limit} differential players (ownership <= {args.max_ownership}%):")
        for _, player in players.iterrows():
            print(f"  {player['name']} ({player['team_name']}) - Ownership: {player['selected_by_percent']}%")


async def analyze_fixtures(args):
    """Analyze fixtures."""
    print("Analyzing fixtures...")
    
    collector = FPLDataCollector()
    await collector.collect_all_data(force_refresh=args.force_refresh)
    processor = collector.processor
    
    fixture_analysis = processor.get_fixture_difficulty_analysis()
    
    if args.team:
        # Filter by specific team
        team_fixtures = fixture_analysis[fixture_analysis['team_name'] == args.team]
        print(f"\nFixture analysis for {args.team}:")
        for _, fixture in team_fixtures.iterrows():
            print(f"  GW{fixture['gameweek']}: vs {fixture['opponent_name']} (Difficulty: {fixture['difficulty']})")
    else:
        # Show all fixtures
        print(f"\nFixture analysis (next 5 gameweeks):")
        for _, fixture in fixture_analysis.head(args.limit).iterrows():
            print(f"  GW{fixture['gameweek']}: {fixture['team_name']} vs {fixture['opponent_name']} (Difficulty: {fixture['difficulty']})")


async def analyze_teams(args):
    """Analyze teams."""
    print("Analyzing teams...")
    
    collector = FPLDataCollector()
    await collector.collect_all_data(force_refresh=args.force_refresh)
    processor = collector.processor
    
    team_analysis = processor.get_team_analysis()
    
    if args.sort_by == "points":
        sorted_teams = team_analysis.nlargest(args.limit, 'points')
    elif args.sort_by == "goals":
        sorted_teams = team_analysis.nlargest(args.limit, 'goals_for')
    elif args.sort_by == "defence":
        sorted_teams = team_analysis.nsmallest(args.limit, 'goals_against')
    else:
        sorted_teams = team_analysis.head(args.limit)
    
    print(f"\nTeam analysis (sorted by {args.sort_by}):")
    for _, team in sorted_teams.iterrows():
        print(f"  {team['team_name']} - Points: {team['points']}, Goals: {team['goals_for']}-{team['goals_against']}, Position: {team['league_position']}")


async def show_injuries(args):
    """Show injury concerns."""
    print("Checking injury concerns...")
    
    collector = FPLDataCollector()
    await collector.collect_all_data(force_refresh=args.force_refresh)
    processor = collector.processor
    
    injuries = processor.get_injury_concerns()
    
    if injuries.empty:
        print("No injury concerns found.")
    else:
        print(f"\nPlayers with injury concerns:")
        for _, player in injuries.head(args.limit).iterrows():
            print(f"  {player['name']} ({player['team_name']}) - Status: {player['status']}")
            if player['news']:
                print(f"    News: {player['news']}")
            if player['chance_of_playing_next_round']:
                print(f"    Chance of playing next round: {player['chance_of_playing_next_round']}%")


async def show_expected_points(args):
    """Show expected points analysis."""
    print("Analyzing expected points...")
    
    collector = FPLDataCollector()
    await collector.collect_all_data(force_refresh=args.force_refresh)
    processor = collector.processor
    
    expected_points = processor.get_expected_points_analysis()
    
    if expected_points.empty:
        print("No expected points data available.")
    else:
        print(f"\nTop {args.limit} players by expected points:")
        for _, player in expected_points.head(args.limit).iterrows():
            print(f"  {player['name']} ({player['team_name']}) - Expected: {player['ep_this']}, Next: {player['ep_next']}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="FPL Data Collector CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached data")
    parser.add_argument("--output-dir", type=Path, default=Path("exports"), help="Output directory for exports")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect FPL data")
    collect_parser.add_argument("--export", action="store_true", help="Export data after collection")
    collect_parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Export format")
    
    # Analyze players command
    players_parser = subparsers.add_parser("players", help="Analyze players")
    players_parser.add_argument("analysis", choices=["top", "value", "form", "transfers", "differentials"], 
                               help="Type of analysis")
    players_parser.add_argument("--limit", type=int, default=10, help="Number of results to show")
    players_parser.add_argument("--min-points", type=int, default=50, help="Minimum points for value/differential analysis")
    players_parser.add_argument("--min-form", type=float, default=5.0, help="Minimum form for form analysis")
    players_parser.add_argument("--min-transfers", type=int, default=1000, help="Minimum transfers for transfer analysis")
    players_parser.add_argument("--max-ownership", type=float, default=5.0, help="Maximum ownership for differential analysis")
    
    # Analyze fixtures command
    fixtures_parser = subparsers.add_parser("fixtures", help="Analyze fixtures")
    fixtures_parser.add_argument("--team", type=str, help="Filter by team name")
    fixtures_parser.add_argument("--limit", type=int, default=20, help="Number of results to show")
    
    # Analyze teams command
    teams_parser = subparsers.add_parser("teams", help="Analyze teams")
    teams_parser.add_argument("--sort-by", choices=["points", "goals", "defence"], default="points", 
                             help="Sort teams by")
    teams_parser.add_argument("--limit", type=int, default=10, help="Number of results to show")
    
    # Show injuries command
    injuries_parser = subparsers.add_parser("injuries", help="Show injury concerns")
    injuries_parser.add_argument("--limit", type=int, default=10, help="Number of results to show")
    
    # Show expected points command
    expected_parser = subparsers.add_parser("expected", help="Show expected points analysis")
    expected_parser.add_argument("--limit", type=int, default=10, help="Number of results to show")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging(args.verbose)
    
    # Run the appropriate command
    if args.command == "collect":
        asyncio.run(collect_data(args))
    elif args.command == "players":
        asyncio.run(analyze_players(args))
    elif args.command == "fixtures":
        asyncio.run(analyze_fixtures(args))
    elif args.command == "teams":
        asyncio.run(analyze_teams(args))
    elif args.command == "injuries":
        asyncio.run(show_injuries(args))
    elif args.command == "expected":
        asyncio.run(show_expected_points(args))


if __name__ == "__main__":
    main()
