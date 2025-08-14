#!/usr/bin/env python3
"""
Quick Start Script for Mustafiness

This script provides a simple way to get started with Mustafiness.
It demonstrates basic usage and shows what data is available.
"""

import asyncio
import logging
from pathlib import Path

from src.collector import collect_fpl_data
from src.models import Position


def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


async def quick_demo():
    """Run a quick demonstration of Mustafiness."""
    print("🚀 Mustafiness - Quick Start Demo")
    print("=" * 50)
    
    try:
        # Collect data
        print("📊 Collecting FPL data...")
        collector = await collect_fpl_data(force_refresh=False, export_format="csv")
        
        # Show summary
        stats = collector.get_summary_stats()
        print(f"\n✅ Data collection completed!")
        print(f"📈 Summary:")
        print(f"   • Total players: {stats['total_players']}")
        print(f"   • Total teams: {stats['total_teams']}")
        print(f"   • Total fixtures: {stats['total_fixtures']}")
        print(f"   • Current gameweek: {stats['current_gameweek']}")
        print(f"   • Next gameweek: {stats['next_gameweek']}")
        
        # Show some quick analysis
        processor = collector.processor
        
        print(f"\n🏆 Top 5 performers:")
        top_players = processor.get_top_performers(top_n=5)
        for i, (_, player) in enumerate(top_players.iterrows(), 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - {player['total_points']} points")
        
        print(f"\n💰 Top 5 value players:")
        value_players = processor.get_value_players(min_points=30, top_n=5)
        for i, (_, player) in enumerate(value_players.iterrows(), 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - {player['points_per_million']:.2f} pts/million")
        
        print(f"\n🔥 Top 5 form players:")
        form_players = processor.get_form_players(min_form=5.0, top_n=5)
        for i, (_, player) in enumerate(form_players.iterrows(), 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - Form: {player['form']:.1f}")
        
        # Show fixture analysis
        current_gw = collector.get_current_gameweek()
        if current_gw:
            next_fixtures = collector.get_fixtures(gameweek=current_gw.id + 1)
            if next_fixtures:
                print(f"\n📅 Next gameweek fixtures (GW{current_gw.id + 1}):")
                for fixture in next_fixtures[:5]:  # Show first 5
                    print(f"   • {fixture.team_h_name} vs {fixture.team_a_name} (Difficulty: {fixture.difficulty})")
        
        # Show export info
        export_dir = Path("exports")
        if export_dir.exists():
            csv_files = list(export_dir.glob("*.csv"))
            print(f"\n📁 Data exported to {export_dir}/")
            print(f"   • {len(csv_files)} CSV files created")
            print(f"   • Ready for analysis!")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"\n💡 Next steps:")
        print(f"   • Run 'python cli.py --help' to see all CLI options")
        print(f"   • Check 'example.py' for more detailed examples")
        print(f"   • Explore the exported CSV files in the 'exports/' directory")
        print(f"   • Read README.md for comprehensive documentation")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        print(f"💡 Make sure you have installed the requirements: pip install -r requirements.txt")


def main():
    """Main function."""
    setup_logging()
    asyncio.run(quick_demo())


if __name__ == "__main__":
    main()
