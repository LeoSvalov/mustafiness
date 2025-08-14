#!/usr/bin/env python3
"""
API Client Example for FPL Data Collector

This script demonstrates how to use the FPL Data Collector API service.
"""

import requests
import json
import time
from typing import Dict, Any


class FPLAPIClient:
    """Client for the Mustafiness API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._make_request("GET", "/health")
    
    def get_status(self) -> Dict[str, Any]:
        """Get API status."""
        return self._make_request("GET", "/status")
    
    def collect_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Collect FPL data."""
        params = {"force_refresh": force_refresh}
        return self._make_request("POST", "/collect", params=params)
    
    def get_players(self, position: str = None, team_id: int = None, limit: int = 100) -> Dict[str, Any]:
        """Get players with optional filtering."""
        params = {"limit": limit}
        if position:
            params["position"] = position
        if team_id:
            params["team_id"] = team_id
        return self._make_request("GET", "/players", params=params)
    
    def get_teams(self) -> Dict[str, Any]:
        """Get all teams."""
        return self._make_request("GET", "/teams")
    
    def get_fixtures(self, gameweek: int = None, limit: int = 100) -> Dict[str, Any]:
        """Get fixtures with optional gameweek filtering."""
        params = {"limit": limit}
        if gameweek:
            params["gameweek"] = gameweek
        return self._make_request("GET", "/fixtures", params=params)
    
    def get_current_gameweek(self) -> Dict[str, Any]:
        """Get current gameweek."""
        return self._make_request("GET", "/current-gameweek")
    
    def get_top_performers(self, position: str = None, metric: str = "total_points", limit: int = 10) -> Dict[str, Any]:
        """Get top performing players."""
        params = {"metric": metric, "limit": limit}
        if position:
            params["position"] = position
        return self._make_request("GET", "/analysis/top-performers", params=params)
    
    def get_value_players(self, position: str = None, min_points: int = 50, limit: int = 10) -> Dict[str, Any]:
        """Get value players."""
        params = {"min_points": min_points, "limit": limit}
        if position:
            params["position"] = position
        return self._make_request("GET", "/analysis/value-players", params=params)
    
    def get_form_players(self, position: str = None, min_form: float = 5.0, limit: int = 10) -> Dict[str, Any]:
        """Get form players."""
        params = {"min_form": min_form, "limit": limit}
        if position:
            params["position"] = position
        return self._make_request("GET", "/analysis/form-players", params=params)
    
    def get_transfer_targets(self, position: str = None, min_transfers: int = 1000, limit: int = 10) -> Dict[str, Any]:
        """Get transfer targets."""
        params = {"min_transfers": min_transfers, "limit": limit}
        if position:
            params["position"] = position
        return self._make_request("GET", "/analysis/transfer-targets", params=params)
    
    def get_differentials(self, position: str = None, max_ownership: float = 5.0, min_points: int = 50, limit: int = 10) -> Dict[str, Any]:
        """Get differential players."""
        params = {"max_ownership": max_ownership, "min_points": min_points, "limit": limit}
        if position:
            params["position"] = position
        return self._make_request("GET", "/analysis/differentials", params=params)
    
    def get_injuries(self, limit: int = 10) -> Dict[str, Any]:
        """Get injury concerns."""
        params = {"limit": limit}
        return self._make_request("GET", "/analysis/injuries", params=params)
    
    def get_fixture_analysis(self, gameweeks: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get fixture analysis."""
        params = {"limit": limit}
        if gameweeks:
            params["gameweeks"] = gameweeks
        return self._make_request("GET", "/analysis/fixtures", params=params)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return self._make_request("GET", "/summary")
    
    def export_csv(self) -> Dict[str, Any]:
        """Export data to CSV."""
        return self._make_request("POST", "/export/csv")
    
    def export_json(self) -> Dict[str, Any]:
        """Export data to JSON."""
        return self._make_request("POST", "/export/json")
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear cache."""
        return self._make_request("POST", "/cache/clear")


def main():
    """Main function demonstrating API usage."""
    print("🚀 FPL Data Collector API Client Example")
    print("=" * 50)
    
    # Initialize client
    client = FPLAPIClient("http://localhost:8000")
    
    # Check health
    print("1. Checking API health...")
    health = client.health_check()
    if health:
        print(f"✅ API is healthy: {health}")
    else:
        print("❌ API is not responding")
        return
    
    # Check status
    print("\n2. Checking API status...")
    status = client.get_status()
    if status:
        print(f"📊 Status: {status['status']}")
        if status.get('data_available'):
            print(f"✅ Data is available")
        else:
            print("⚠️  No data available, collecting...")
            collect_result = client.collect_data()
            if collect_result:
                print(f"✅ Data collection: {collect_result['status']}")
                if collect_result['status'] == 'started':
                    print("⏳ Data collection started in background, waiting...")
                    time.sleep(10)  # Wait a bit for collection to complete
    
    # Get summary stats
    print("\n3. Getting summary statistics...")
    summary = client.get_summary_stats()
    if summary:
        print(f"📈 Summary:")
        print(f"   • Total players: {summary['total_players']}")
        print(f"   • Total teams: {summary['total_teams']}")
        print(f"   • Current gameweek: {summary['current_gameweek']}")
        print(f"   • Next gameweek: {summary['next_gameweek']}")
    
    # Get top performers
    print("\n4. Getting top 5 performers...")
    top_performers = client.get_top_performers(limit=5)
    if top_performers and top_performers.get('players'):
        print("🏆 Top 5 performers:")
        for i, player in enumerate(top_performers['players'][:5], 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - {player['total_points']} points")
    
    # Get value players
    print("\n5. Getting top 5 value players...")
    value_players = client.get_value_players(min_points=30, limit=5)
    if value_players and value_players.get('players'):
        print("💰 Top 5 value players:")
        for i, player in enumerate(value_players['players'][:5], 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - {player['price']}M")
    
    # Get form players
    print("\n6. Getting top 5 form players...")
    form_players = client.get_form_players(min_form=5.0, limit=5)
    if form_players and form_players.get('players'):
        print("🔥 Top 5 form players:")
        for i, player in enumerate(form_players['players'][:5], 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - Form: {player['form']}")
    
    # Get transfer targets
    print("\n7. Getting top 5 transfer targets...")
    transfer_targets = client.get_transfer_targets(min_transfers=5000, limit=5)
    if transfer_targets and transfer_targets.get('players'):
        print("📈 Top 5 transfer targets:")
        for i, player in enumerate(transfer_targets['players'][:5], 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - Transfers in: {player['transfers_in']}")
    
    # Get differentials
    print("\n8. Getting top 5 differentials...")
    differentials = client.get_differentials(max_ownership=3.0, min_points=50, limit=5)
    if differentials and differentials.get('players'):
        print("🎯 Top 5 differentials:")
        for i, player in enumerate(differentials['players'][:5], 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - Ownership: {player['selected_by_percent']}%")
    
    # Get injuries
    print("\n9. Getting injury concerns...")
    injuries = client.get_injuries(limit=5)
    if injuries and injuries.get('players'):
        print("🏥 Top 5 injury concerns:")
        for i, player in enumerate(injuries['players'][:5], 1):
            print(f"   {i}. {player['name']} ({player['team_name']}) - Status: {player['status']}")
            if player.get('news'):
                print(f"      News: {player['news']}")
    
    # Get current gameweek
    print("\n10. Getting current gameweek...")
    current_gw = client.get_current_gameweek()
    if current_gw:
        print(f"📅 Current gameweek: {current_gw['name']} (ID: {current_gw['id']})")
        print(f"   Deadline: {current_gw['deadline_time']}")
    
    # Get fixtures for next gameweek
    if current_gw:
        print(f"\n11. Getting fixtures for GW{current_gw['id'] + 1}...")
        fixtures = client.get_fixtures(gameweek=current_gw['id'] + 1, limit=5)
        if fixtures:
            print(f"📅 Next gameweek fixtures:")
            for i, fixture in enumerate(fixtures[:5], 1):
                print(f"   {i}. {fixture['team_h_name']} vs {fixture['team_a_name']} (Difficulty: {fixture['difficulty']})")
    
    # Export data
    print("\n12. Exporting data to CSV...")
    export_result = client.export_csv()
    if export_result:
        print(f"✅ Export result: {export_result['message']}")
    
    print("\n🎉 API client example completed!")
    print("\n💡 You can also:")
    print("   • Visit http://localhost:8000/docs for interactive API documentation")
    print("   • Use the API endpoints in your own applications")
    print("   • Integrate with other tools and services")


if __name__ == "__main__":
    main()
