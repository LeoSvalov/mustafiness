#!/usr/bin/env python3
"""
Example script demonstrating the Squad Builder functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api_client import FPLAPIClient
from src.data_processor import FPLDataProcessor
from src.squad_builder import SquadBuilder, SquadConstraints
from src.ml_squad_builder import MLSquadBuilder
from src.squad_builder_service import SquadBuilderService, SquadConstraintsRequest
from src.models import Position


def main():
    """Main function demonstrating squad builder usage."""
    print("🚀 Fantasy Premier League Squad Builder Example")
    print("=" * 50)
    
    try:
        # Initialize API client and fetch data
        print("📡 Fetching FPL data...")
        client = FPLAPIClient()
        fpl_data = client.get_all_data()
        
        print(f"✅ Fetched data for {len(fpl_data.players)} players, {len(fpl_data.teams)} teams")
        
        # Initialize squad builder service
        squad_service = SquadBuilderService(fpl_data)
        
        # Example 1: Basic squad building
        print("\n🎯 Example 1: Basic Squad Building")
        print("-" * 30)
        
        basic_constraints = SquadConstraintsRequest(
            budget=100.0,
            max_players_per_team=3,
            formation="4-4-2"
        )
        
        basic_result = squad_service.build_squad(basic_constraints, use_ml=False)
        
        print(f"Strategy used: {basic_result.strategy_used}")
        print(f"Total cost: £{basic_result.analysis.get('total_cost', 0):.1f}m")
        print(f"Expected points: {basic_result.analysis.get('total_expected_points', 0):.1f}")
        print(f"Average form: {basic_result.analysis.get('form_analysis', {}).get('avg_form', 0):.2f}")
        
        print("\nSelected squad:")
        for i, player in enumerate(basic_result.squad[:11], 1):  # Show starting 11
            print(f"{i:2d}. {player['name']} ({player['position']}) - £{player['price']:.1f}m - {player['team_name']}")
        
        # Example 2: ML-optimized squad building
        print("\n🤖 Example 2: ML-Optimized Squad Building")
        print("-" * 40)
        
        ml_result = squad_service.build_squad(basic_constraints, use_ml=True)
        
        print(f"Strategy used: {ml_result.strategy_used}")
        print(f"Total cost: £{ml_result.analysis.get('total_cost', 0):.1f}m")
        print(f"Expected points: {ml_result.analysis.get('total_expected_points', 0):.1f}")
        
        # Show ML-specific analysis
        ml_analysis = ml_result.analysis.get('ml_analysis', {})
        if ml_analysis:
            print(f"ML Predicted points: {ml_analysis.get('total_predicted_points', 0):.1f}")
            print(f"Market efficiency: {ml_analysis.get('avg_market_efficiency', 0):.2f}")
            print(f"Cluster diversity: {len(ml_analysis.get('cluster_distribution', {}))} clusters")
        
        print("\nML-optimized squad:")
        for i, player in enumerate(ml_result.squad[:11], 1):
            predicted = player.get('predicted_points', 'N/A')
            print(f"{i:2d}. {player['name']} ({player['position']}) - £{player['price']:.1f}m - Pred: {predicted}")
        
        # Example 3: Captain recommendations
        print("\n👑 Example 3: Captain Recommendations")
        print("-" * 35)
        
        squad_player_ids = [player['player_id'] for player in basic_result.squad]
        captain_recs = squad_service.get_captain_recommendations(squad_player_ids, 5)
        
        print("Top captain candidates:")
        for i, rec in enumerate(captain_recs, 1):
            print(f"{i}. {rec['name']} - Form: {rec['form_score']:.2f}, Fixtures: {rec['fixture_difficulty_score']:.2f}")
        
        # Example 4: Transfer recommendations
        print("\n🔄 Example 4: Transfer Recommendations")
        print("-" * 35)
        
        # Simulate a current squad with some underperforming players
        current_squad = squad_player_ids[:10] + [123, 456, 789]  # Add some dummy IDs
        
        transfer_recs = squad_service.get_transfer_recommendations(
            current_squad, basic_constraints, num_recommendations=5, use_ml=True
        )
        
        print("Top transfer recommendations:")
        for i, rec in enumerate(transfer_recs, 1):
            print(f"{i}. {rec.transfer_out['name']} → {rec.transfer_in['name']}")
            print(f"   Upgrade value: {rec.upgrade_value:.3f}, Price diff: £{rec.price_difference:.1f}m")
        
        # Example 5: Player analysis
        print("\n📊 Example 5: Player Analysis")
        print("-" * 25)
        
        if basic_result.squad:
            top_player_id = basic_result.squad[0]['player_id']
            player_analysis = squad_service.get_player_analysis(top_player_id)
            
            print(f"Analysis for {player_analysis['name']}:")
            print(f"Position: {player_analysis['position']}")
            print(f"Team: {player_analysis['team_name']}")
            print(f"Price: £{player_analysis['price']:.1f}m")
            print(f"Total score: {player_analysis['total_score']:.3f}")
            print(f"Form score: {player_analysis['form_score']:.3f}")
            print(f"Fixture difficulty: {player_analysis['fixture_difficulty_score']:.3f}")
            print(f"Risk factor: {player_analysis['risk_factor']:.3f}")
            
            if 'predicted_points' in player_analysis:
                print(f"ML Predicted points: {player_analysis['predicted_points']:.1f}")
                print(f"Market efficiency: {player_analysis.get('market_efficiency_score', 0):.2f}")
        
        # Example 6: Squad comparison
        print("\n⚖️ Example 6: Squad Comparison")
        print("-" * 30)
        
        squad1_ids = [player['player_id'] for player in basic_result.squad]
        squad2_ids = [player['player_id'] for player in ml_result.squad]
        
        comparison = squad_service.get_squad_comparison(squad1_ids, squad2_ids)
        
        print("Squad Comparison (Basic vs ML):")
        print(f"Cost difference: £{comparison['differences']['cost_difference']:.1f}m")
        print(f"Points difference: {comparison['differences']['points_difference']:.1f}")
        print(f"Form difference: {comparison['differences']['form_difference']:.3f}")
        print(f"Risk difference: {comparison['differences']['risk_difference']:.3f}")
        
        # Example 7: Custom constraints
        print("\n🎛️ Example 7: Custom Constraints")
        print("-" * 30)
        
        custom_constraints = SquadConstraintsRequest(
            budget=95.0,  # Lower budget
            max_players_per_team=2,  # More team diversity
            formation="3-5-2",  # Different formation
            must_have_players=[1, 2, 3],  # Must include specific players (if they exist)
            min_players_per_position={
                "GK": 2,
                "DEF": 3,  # Fewer defenders
                "MID": 5,  # More midfielders
                "FWD": 3
            }
        )
        
        custom_result = squad_service.build_squad(custom_constraints, use_ml=True)
        
        print(f"Custom squad cost: £{custom_result.analysis.get('total_cost', 0):.1f}m")
        print(f"Custom squad points: {custom_result.analysis.get('total_expected_points', 0):.1f}")
        
        print("\nCustom formation (3-5-2):")
        for i, player in enumerate(custom_result.squad[:11], 1):
            print(f"{i:2d}. {player['name']} ({player['position']}) - £{player['price']:.1f}m")
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
