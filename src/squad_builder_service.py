"""
Squad Builder Service for Fantasy Premier League API.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Query
from pydantic import BaseModel

from .models import Position, FPLData
from .data_processor import FPLDataProcessor
from .squad_builder import SquadBuilder, SquadConstraints
from .ml_squad_builder import MLSquadBuilder
from .exceptions import DataProcessingError


class SquadConstraintsRequest(BaseModel):
    """Request model for squad constraints."""
    budget: float = 100.0
    max_players_per_team: int = 3
    formation: Optional[str] = None
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None
    must_have_players: List[int] = []
    must_not_have_players: List[int] = []
    min_players_per_position: Dict[str, int] = {
        "GK": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3
    }
    max_players_per_position: Dict[str, int] = {
        "GK": 2,
        "DEF": 5,
        "MID": 5,
        "FWD": 3
    }


class SquadBuilderResponse(BaseModel):
    """Response model for squad builder."""
    squad: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    constraints_used: Dict[str, Any]
    strategy_used: str
    alternatives: Optional[List[Dict[str, Any]]] = None


class TransferRecommendation(BaseModel):
    """Transfer recommendation model."""
    transfer_out: Dict[str, Any]
    transfer_in: Dict[str, Any]
    upgrade_value: float
    price_difference: float
    position: str
    confidence: Optional[Dict[str, float]] = None


class SquadBuilderService:
    """Service for squad building operations."""
    
    def __init__(self, fpl_data: FPLData):
        """Initialize the squad builder service."""
        self.data = fpl_data
        self.processor = FPLDataProcessor(fpl_data)
        self.squad_builder = SquadBuilder(fpl_data, self.processor)
        self.ml_squad_builder = MLSquadBuilder(fpl_data, self.processor)
    
    def build_squad(self, constraints: SquadConstraintsRequest, use_ml: bool = False) -> SquadBuilderResponse:
        """Build an optimal squad based on constraints."""
        try:
            # Convert request to internal constraints
            internal_constraints = self._convert_constraints(constraints)
            
            if use_ml:
                result = self.ml_squad_builder.build_ml_optimized_squad(internal_constraints)
                strategy = "ml_optimized"
            else:
                result = self.squad_builder.build_optimal_squad(internal_constraints)
                strategy = "standard"
            
            # Convert squad to response format
            squad_data = self._convert_squad_to_response(result['squad'])
            
            return SquadBuilderResponse(
                squad=squad_data,
                analysis=result.get('analysis', {}),
                constraints_used=constraints.dict(),
                strategy_used=strategy,
                alternatives=result.get('all_strategies') if not use_ml else None
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Squad building failed: {str(e)}")
    
    def get_captain_recommendations(self, squad_player_ids: List[int], num_recommendations: int = 5) -> List[Dict[str, Any]]:
        """Get captain recommendations for a squad."""
        try:
            squad = [self.squad_builder.player_scores[pid] for pid in squad_player_ids if pid in self.squad_builder.player_scores]
            recommendations = self.squad_builder.get_captain_recommendations(squad, num_recommendations)
            
            return [
                {
                    'player_id': rec.player_id,
                    'name': rec.name,
                    'position': rec.position.value,
                    'team_id': rec.team_id,
                    'price': rec.price,
                    'total_score': rec.total_score,
                    'form_score': rec.form_score,
                    'fixture_difficulty_score': rec.fixture_difficulty_score,
                    'expected_points': rec.expected_points
                }
                for rec in recommendations
            ]
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Captain recommendations failed: {str(e)}")
    
    def get_transfer_recommendations(self, current_squad: List[int], 
                                   constraints: SquadConstraintsRequest,
                                   num_recommendations: int = 10,
                                   use_ml: bool = False) -> List[TransferRecommendation]:
        """Get transfer recommendations for current squad."""
        try:
            internal_constraints = self._convert_constraints(constraints)
            
            if use_ml:
                recommendations = self.ml_squad_builder.get_ml_transfer_recommendations(
                    current_squad, internal_constraints, num_recommendations
                )
            else:
                recommendations = self.squad_builder.get_transfer_recommendations(
                    current_squad, internal_constraints, num_recommendations
                )
            
            return [
                TransferRecommendation(
                    transfer_out=self._player_score_to_dict(rec['transfer_out']),
                    transfer_in=self._player_score_to_dict(rec['transfer_in']),
                    upgrade_value=rec['upgrade_value'],
                    price_difference=rec['price_difference'],
                    position=rec['position'],
                    confidence=rec.get('confidence')
                )
                for rec in recommendations
            ]
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transfer recommendations failed: {str(e)}")
    
    def get_player_analysis(self, player_id: int) -> Dict[str, Any]:
        """Get detailed analysis for a specific player."""
        try:
            if player_id not in self.squad_builder.player_scores:
                raise HTTPException(status_code=404, detail="Player not found")
            
            player_score = self.squad_builder.player_scores[player_id]
            player = self.data.get_player_by_id(player_id)
            team = self.data.get_team_by_id(player.team) if player else None
            
            analysis = {
                'player_id': player_id,
                'name': player_score.name,
                'position': player_score.position.value,
                'team_id': player_score.team_id,
                'team_name': team.name if team else None,
                'price': player_score.price,
                'total_score': player_score.total_score,
                'form_score': player_score.form_score,
                'fixture_difficulty_score': player_score.fixture_difficulty_score,
                'team_strength_score': player_score.team_strength_score,
                'differential_score': player_score.differential_score,
                'expected_points': player_score.expected_points,
                'risk_factor': player_score.risk_factor,
            }
            
            # Add ML-specific analysis if available
            if hasattr(player_score, 'predicted_points'):
                analysis.update({
                    'predicted_points': player_score.predicted_points,
                    'confidence_interval': player_score.confidence_interval,
                    'cluster_id': player_score.cluster_id,
                    'similarity_score': player_score.similarity_score,
                    'market_efficiency_score': player_score.market_efficiency_score,
                })
            
            # Add upcoming fixtures
            upcoming_fixtures = self.squad_builder._get_upcoming_fixtures(player_score.team_id, 5)
            analysis['upcoming_fixtures'] = [
                {
                    'gameweek': f.event,
                    'opponent': self.data.get_team_by_id(f.team_a if f.team_h == player_score.team_id else f.team_h).name,
                    'is_home': f.team_h == player_score.team_id,
                    'difficulty': f.difficulty,
                    'kickoff_time': f.kickoff_time.isoformat() if f.kickoff_time else None
                }
                for f in upcoming_fixtures
            ]
            
            return analysis
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Player analysis failed: {str(e)}")
    
    def get_squad_comparison(self, squad1: List[int], squad2: List[int]) -> Dict[str, Any]:
        """Compare two squads."""
        try:
            squad1_players = [self.squad_builder.player_scores[pid] for pid in squad1 if pid in self.squad_builder.player_scores]
            squad2_players = [self.squad_builder.player_scores[pid] for pid in squad2 if pid in self.squad_builder.player_scores]
            
            # Calculate metrics for both squads
            squad1_analysis = self.squad_builder._analyze_squad(squad1_players, SquadConstraints())
            squad2_analysis = self.squad_builder._analyze_squad(squad2_players, SquadConstraints())
            
            comparison = {
                'squad1': {
                    'player_count': len(squad1_players),
                    'total_cost': squad1_analysis.get('total_cost', 0),
                    'total_expected_points': squad1_analysis.get('total_expected_points', 0),
                    'avg_form': squad1_analysis.get('form_analysis', {}).get('avg_form', 0),
                    'avg_risk': squad1_analysis.get('risk_analysis', {}).get('avg_risk', 0),
                    'position_distribution': squad1_analysis.get('position_distribution', {}),
                    'team_distribution': squad1_analysis.get('team_distribution', {})
                },
                'squad2': {
                    'player_count': len(squad2_players),
                    'total_cost': squad2_analysis.get('total_cost', 0),
                    'total_expected_points': squad2_analysis.get('total_expected_points', 0),
                    'avg_form': squad2_analysis.get('form_analysis', {}).get('avg_form', 0),
                    'avg_risk': squad2_analysis.get('risk_analysis', {}).get('avg_risk', 0),
                    'position_distribution': squad2_analysis.get('position_distribution', {}),
                    'team_distribution': squad2_analysis.get('team_distribution', {})
                },
                'differences': {
                    'cost_difference': squad1_analysis.get('total_cost', 0) - squad2_analysis.get('total_cost', 0),
                    'points_difference': squad1_analysis.get('total_expected_points', 0) - squad2_analysis.get('total_expected_points', 0),
                    'form_difference': squad1_analysis.get('form_analysis', {}).get('avg_form', 0) - squad2_analysis.get('form_analysis', {}).get('avg_form', 0),
                    'risk_difference': squad1_analysis.get('risk_analysis', {}).get('avg_risk', 0) - squad2_analysis.get('risk_analysis', {}).get('avg_risk', 0)
                }
            }
            
            return comparison
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Squad comparison failed: {str(e)}")
    
    def _convert_constraints(self, constraints: SquadConstraintsRequest) -> SquadConstraints:
        """Convert API constraints to internal constraints."""
        min_players = {}
        max_players = {}
        
        for pos_str, count in constraints.min_players_per_position.items():
            min_players[Position(pos_str)] = count
        
        for pos_str, count in constraints.max_players_per_position.items():
            max_players[Position(pos_str)] = count
        
        return SquadConstraints(
            budget=constraints.budget,
            max_players_per_team=constraints.max_players_per_team,
            formation=constraints.formation,
            captain_id=constraints.captain_id,
            vice_captain_id=constraints.vice_captain_id,
            must_have_players=constraints.must_have_players,
            must_not_have_players=constraints.must_not_have_players,
            min_players_per_position=min_players,
            max_players_per_position=max_players
        )
    
    def _convert_squad_to_response(self, squad: List) -> List[Dict[str, Any]]:
        """Convert squad to response format."""
        return [
            {
                'player_id': player.player_id,
                'name': player.name,
                'position': player.position.value,
                'team_id': player.team_id,
                'team_name': self.data.get_team_by_id(player.team_id).name if self.data.get_team_by_id(player.team_id) else None,
                'price': player.price,
                'total_score': player.total_score,
                'form_score': player.form_score,
                'fixture_difficulty_score': player.fixture_difficulty_score,
                'team_strength_score': player.team_strength_score,
                'differential_score': player.differential_score,
                'expected_points': player.expected_points,
                'risk_factor': player.risk_factor,
                'predicted_points': getattr(player, 'predicted_points', None),
                'market_efficiency_score': getattr(player, 'market_efficiency_score', None),
                'cluster_id': getattr(player, 'cluster_id', None),
            }
            for player in squad
        ]
    
    def _player_score_to_dict(self, player_score) -> Dict[str, Any]:
        """Convert player score to dictionary."""
        return {
            'player_id': player_score.player_id,
            'name': player_score.name,
            'position': player_score.position.value,
            'team_id': player_score.team_id,
            'price': player_score.price,
            'total_score': player_score.total_score,
            'expected_points': player_score.expected_points,
            'predicted_points': getattr(player_score, 'predicted_points', None),
        }
