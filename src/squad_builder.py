"""
Squad Builder for Fantasy Premier League using data science and ML approaches.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from .models import Player, Team, Fixture, Position, FPLData
from .data_processor import FPLDataProcessor
from .exceptions import DataProcessingError


@dataclass
class SquadConstraints:
    """Constraints for squad building."""
    budget: float = 100.0  # £100 million budget
    max_players_per_team: int = 3
    formation: Optional[str] = None  # e.g., "4-4-2", "3-5-2", etc.
    captain_id: Optional[int] = None
    vice_captain_id: Optional[int] = None
    must_have_players: List[int] = None  # Player IDs that must be included
    must_not_have_players: List[int] = None  # Player IDs to exclude
    min_players_per_position: Dict[Position, int] = None
    max_players_per_position: Dict[Position, int] = None


@dataclass
class PlayerScore:
    """Player scoring model for optimization."""
    player_id: int
    name: str
    position: Position
    team_id: int
    price: float
    expected_points: float
    form_score: float
    fixture_difficulty_score: float
    team_strength_score: float
    differential_score: float
    total_score: float
    risk_factor: float


class SquadBuilder:
    """
    Advanced squad builder using data science and machine learning approaches.
    """
    
    def __init__(self, fpl_data: FPLData, processor: FPLDataProcessor):
        """Initialize the squad builder."""
        self.data = fpl_data
        self.processor = processor
        self.player_scores = {}
        self._calculate_player_scores()
    
    def _calculate_player_scores(self):
        """Calculate comprehensive player scores using multiple factors."""
        for player in self.data.players:
            if player.status != 'a':  # Skip unavailable players
                continue
            
            # Get player's team and upcoming fixtures
            team = self.data.get_team_by_id(player.team)
            upcoming_fixtures = self._get_upcoming_fixtures(player.team, 5)  # Next 5 GWs
            
            # Calculate various scoring components
            form_score = self._calculate_form_score(player)
            fixture_score = self._calculate_fixture_difficulty_score(player, upcoming_fixtures)
            team_strength_score = self._calculate_team_strength_score(player, team)
            differential_score = self._calculate_differential_score(player)
            expected_points_score = self._calculate_expected_points_score(player)
            risk_factor = self._calculate_risk_factor(player)
            
            # Weighted combination of scores
            total_score = (
                0.25 * form_score +
                0.20 * fixture_score +
                0.15 * team_strength_score +
                0.15 * differential_score +
                0.20 * expected_points_score +
                0.05 * (1 - risk_factor)  # Lower risk is better
            )
            
            self.player_scores[player.id] = PlayerScore(
                player_id=player.id,
                name=player.full_name,
                position=player.position,
                team_id=player.team,
                price=player.price,
                expected_points=expected_points_score,
                form_score=form_score,
                fixture_difficulty_score=fixture_score,
                team_strength_score=team_strength_score,
                differential_score=differential_score,
                total_score=total_score,
                risk_factor=risk_factor
            )
    
    def _calculate_form_score(self, player: Player) -> float:
        """Calculate form score based on recent performance."""
        if not player.form:
            return 0.0
        
        form = float(player.form)
        
        # Normalize form score (typically 0-10, but can be higher)
        if form > 0:
            return min(form / 10.0, 1.0)
        return 0.0
    
    def _calculate_fixture_difficulty_score(self, player: Player, fixtures: List[Fixture]) -> float:
        """Calculate fixture difficulty score for upcoming games."""
        if not fixtures:
            return 0.5  # Neutral score if no fixtures
        
        # FPL difficulty: 1=easy, 2=medium, 3=hard, 4=very hard, 5=extremely hard
        # We want easier fixtures, so invert the difficulty
        difficulty_scores = []
        
        for fixture in fixtures:
            if fixture.team_h == player.team:
                # Home fixture
                difficulty = fixture.difficulty
                is_home = True
            else:
                # Away fixture
                difficulty = fixture.difficulty
                is_home = False
            
            # Convert difficulty to score (easier = higher score)
            base_score = (6 - difficulty) / 5.0  # 1.0 for difficulty 1, 0.2 for difficulty 5
            
            # Home advantage bonus
            if is_home:
                base_score *= 1.1
            
            difficulty_scores.append(base_score)
        
        # Weight recent fixtures more heavily
        weights = np.linspace(1.0, 0.5, len(difficulty_scores))
        weighted_score = np.average(difficulty_scores, weights=weights)
        
        return min(weighted_score, 1.0)
    
    def _calculate_team_strength_score(self, player: Player, team: Team) -> float:
        """Calculate team strength score."""
        if not team:
            return 0.5
        
        # Normalize team strength (typically 1000-1500)
        strength_score = (team.strength - 1000) / 500.0
        strength_score = max(0.0, min(1.0, strength_score))
        
        # Consider league position
        position_score = max(0.0, (21 - team.position) / 20.0)  # 1st = 1.0, 20th = 0.05
        
        # Consider goals scored/conceded based on position
        if player.position in [Position.MID, Position.FWD]:
            # Attackers benefit from goals scored
            goals_score = min(team.goals_for / 50.0, 1.0)  # Normalize to 50 goals
        else:
            # Defenders/GKs benefit from clean sheets (fewer goals conceded)
            goals_score = max(0.0, (50 - team.goals_against) / 50.0)
        
        return (strength_score + position_score + goals_score) / 3.0
    
    def _calculate_differential_score(self, player: Player) -> float:
        """Calculate differential score (lower ownership = higher score)."""
        if not player.selected_by_percent:
            return 0.5  # Neutral score
        
        ownership = float(player.selected_by_percent)
        
        # Lower ownership is better for differentials
        # 0% ownership = 1.0, 50%+ ownership = 0.0
        if ownership <= 5:
            return 1.0
        elif ownership >= 50:
            return 0.0
        else:
            return 1.0 - (ownership / 50.0)
    
    def _calculate_expected_points_score(self, player: Player) -> float:
        """Calculate expected points score."""
        if not player.ep_this:
            return 0.5  # Neutral score
        
        expected_points = float(player.ep_this)
        
        # Normalize expected points (typically 0-10)
        return min(expected_points / 10.0, 1.0)
    
    def _calculate_risk_factor(self, player: Player) -> float:
        """Calculate risk factor (0=low risk, 1=high risk)."""
        risk = 0.0
        
        # Injury/availability risk
        if player.status != 'a':
            risk += 0.5
        
        if player.news:
            risk += 0.3
        
        if player.chance_of_playing_next_round and player.chance_of_playing_next_round < 100:
            risk += (100 - player.chance_of_playing_next_round) / 100.0
        
        # Price volatility risk
        if player.cost_change_event != 0:
            risk += 0.1
        
        # Transfer risk (high transfers out might indicate issues)
        if player.transfers_out > player.transfers_in * 2:
            risk += 0.2
        
        return min(risk, 1.0)
    
    def _get_upcoming_fixtures(self, team_id: int, num_gameweeks: int = 5) -> List[Fixture]:
        """Get upcoming fixtures for a team."""
        current_gw = self.data.current_gameweek
        if not current_gw:
            return []
        
        upcoming_fixtures = []
        for gw in range(current_gw.id + 1, min(current_gw.id + 1 + num_gameweeks, 39)):
            gw_fixtures = self.data.get_fixtures_by_gameweek(gw)
            for fixture in gw_fixtures:
                if fixture.team_h == team_id or fixture.team_a == team_id:
                    upcoming_fixtures.append(fixture)
        
        return upcoming_fixtures
    
    def build_optimal_squad(self, constraints: SquadConstraints) -> Dict[str, Any]:
        """
        Build optimal squad using multiple optimization strategies.
        """
        # Initialize constraints
        if constraints.min_players_per_position is None:
            constraints.min_players_per_position = {
                Position.GK: 2,
                Position.DEF: 5,
                Position.MID: 5,
                Position.FWD: 3
            }
        
        if constraints.max_players_per_position is None:
            constraints.max_players_per_position = {
                Position.GK: 2,
                Position.DEF: 5,
                Position.MID: 5,
                Position.FWD: 3
            }
        
        # Strategy 1: Value-based optimization
        value_squad = self._build_value_squad(constraints)
        
        # Strategy 2: Form-based optimization
        form_squad = self._build_form_squad(constraints)
        
        # Strategy 3: Fixture-based optimization
        fixture_squad = self._build_fixture_squad(constraints)
        
        # Strategy 4: Differential optimization
        differential_squad = self._build_differential_squad(constraints)
        
        # Strategy 5: Balanced optimization (ensemble)
        balanced_squad = self._build_balanced_squad(constraints)
        
        # Evaluate all squads and return the best one
        squads = {
            'value': value_squad,
            'form': form_squad,
            'fixture': fixture_squad,
            'differential': differential_squad,
            'balanced': balanced_squad
        }
        
        best_squad = self._evaluate_squads(squads, constraints)
        
        return {
            'squad': best_squad,
            'all_strategies': squads,
            'analysis': self._analyze_squad(best_squad, constraints)
        }
    
    def _build_value_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad based on value (points per million)."""
        available_players = list(self.player_scores.values())
        
        # Calculate value score (points per million)
        for player in available_players:
            player.total_score = (player.expected_points / player.price) * 10
        
        return self._select_players_by_constraints(available_players, constraints)
    
    def _build_form_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad based on current form."""
        available_players = list(self.player_scores.values())
        
        # Sort by form score
        for player in available_players:
            player.total_score = player.form_score
        
        return self._select_players_by_constraints(available_players, constraints)
    
    def _build_fixture_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad based on fixture difficulty."""
        available_players = list(self.player_scores.values())
        
        # Sort by fixture difficulty score
        for player in available_players:
            player.total_score = player.fixture_difficulty_score
        
        return self._select_players_by_constraints(available_players, constraints)
    
    def _build_differential_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad based on differential potential."""
        available_players = list(self.player_scores.values())
        
        # Sort by differential score
        for player in available_players:
            player.total_score = player.differential_score
        
        return self._select_players_by_constraints(available_players, constraints)
    
    def _build_balanced_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build balanced squad using ensemble approach."""
        available_players = list(self.player_scores.values())
        
        # Use the pre-calculated balanced total_score
        return self._select_players_by_constraints(available_players, constraints)
    
    def _select_players_by_constraints(self, players: List[PlayerScore], 
                                     constraints: SquadConstraints) -> List[PlayerScore]:
        """Select players based on FPL constraints."""
        # Sort by total score
        players.sort(key=lambda x: x.total_score, reverse=True)
        
        selected_players = []
        remaining_budget = constraints.budget
        team_counts = {}
        
        # Handle must-have players first
        if constraints.must_have_players:
            for player_id in constraints.must_have_players:
                if player_id in self.player_scores:
                    player = self.player_scores[player_id]
                    if player.price <= remaining_budget:
                        selected_players.append(player)
                        remaining_budget -= player.price
                        team_counts[player.team_id] = team_counts.get(player.team_id, 0) + 1
        
        # Select players by position
        for position in [Position.GK, Position.DEF, Position.MID, Position.FWD]:
            min_count = constraints.min_players_per_position[position]
            max_count = constraints.max_players_per_position[position]
            
            position_players = [p for p in players if p.position == position]
            selected_count = len([p for p in selected_players if p.position == position])
            
            # Select additional players for this position
            for player in position_players:
                if selected_count >= max_count:
                    break
                
                if player.player_id in constraints.must_not_have_players:
                    continue
                
                if player.price > remaining_budget:
                    continue
                
                if team_counts.get(player.team_id, 0) >= constraints.max_players_per_team:
                    continue
                
                selected_players.append(player)
                remaining_budget -= player.price
                team_counts[player.team_id] = team_counts.get(player.team_id, 0) + 1
                selected_count += 1
        
        return selected_players[:15]  # Ensure exactly 15 players
    
    def _evaluate_squads(self, squads: Dict[str, List[PlayerScore]], 
                        constraints: SquadConstraints) -> List[PlayerScore]:
        """Evaluate and rank different squad strategies."""
        squad_scores = {}
        
        for strategy, squad in squads.items():
            if len(squad) != 15:  # Invalid squad
                squad_scores[strategy] = 0
                continue
            
            # Calculate squad metrics
            total_cost = sum(p.price for p in squad)
            total_expected_points = sum(p.expected_points for p in squad)
            avg_form = np.mean([p.form_score for p in squad])
            avg_fixture_difficulty = np.mean([p.fixture_difficulty_score for p in squad])
            avg_risk = np.mean([p.risk_factor for p in squad])
            
            # Calculate squad diversity (teams represented)
            teams = set(p.team_id for p in squad)
            team_diversity = len(teams) / 15.0
            
            # Calculate position balance
            position_counts = {}
            for p in squad:
                position_counts[p.position] = position_counts.get(p.position, 0) + 1
            
            position_balance = 1.0
            if position_counts.get(Position.GK, 0) != 2:
                position_balance -= 0.2
            if position_counts.get(Position.DEF, 0) < 3 or position_counts.get(Position.DEF, 0) > 5:
                position_balance -= 0.2
            if position_counts.get(Position.MID, 0) < 3 or position_counts.get(Position.MID, 0) > 5:
                position_balance -= 0.2
            if position_counts.get(Position.FWD, 0) < 1 or position_counts.get(Position.FWD, 0) > 3:
                position_balance -= 0.2
            
            # Calculate overall score
            score = (
                0.25 * (total_expected_points / 15.0) +  # Expected points
                0.20 * avg_form +  # Form
                0.20 * avg_fixture_difficulty +  # Fixture difficulty
                0.15 * team_diversity +  # Team diversity
                0.10 * position_balance +  # Position balance
                0.10 * (1 - avg_risk)  # Risk factor
            )
            
            # Penalty for budget overrun
            if total_cost > constraints.budget:
                score *= 0.5
            
            squad_scores[strategy] = score
        
        # Return the best squad
        best_strategy = max(squad_scores, key=squad_scores.get)
        return squads[best_strategy]
    
    def _analyze_squad(self, squad: List[PlayerScore], 
                      constraints: SquadConstraints) -> Dict[str, Any]:
        """Analyze the selected squad."""
        if not squad:
            return {}
        
        total_cost = sum(p.price for p in squad)
        total_expected_points = sum(p.expected_points for p in squad)
        
        # Position distribution
        position_counts = {}
        for p in squad:
            position_counts[p.position.value] = position_counts.get(p.position.value, 0) + 1
        
        # Team distribution
        team_counts = {}
        for p in squad:
            team_counts[p.team_id] = team_counts.get(p.team_id, 0) + 1
        
        # Risk analysis
        high_risk_players = [p for p in squad if p.risk_factor > 0.7]
        medium_risk_players = [p for p in squad if 0.3 < p.risk_factor <= 0.7]
        low_risk_players = [p for p in squad if p.risk_factor <= 0.3]
        
        # Form analysis
        high_form_players = [p for p in squad if p.form_score > 0.7]
        medium_form_players = [p for p in squad if 0.3 < p.form_score <= 0.7]
        low_form_players = [p for p in squad if p.form_score <= 0.3]
        
        return {
            'total_cost': total_cost,
            'remaining_budget': constraints.budget - total_cost,
            'total_expected_points': total_expected_points,
            'avg_expected_points': total_expected_points / len(squad),
            'position_distribution': position_counts,
            'team_distribution': team_counts,
            'risk_analysis': {
                'high_risk': len(high_risk_players),
                'medium_risk': len(medium_risk_players),
                'low_risk': len(low_risk_players),
                'avg_risk': np.mean([p.risk_factor for p in squad])
            },
            'form_analysis': {
                'high_form': len(high_form_players),
                'medium_form': len(medium_form_players),
                'low_form': len(low_form_players),
                'avg_form': np.mean([p.form_score for p in squad])
            },
            'fixture_analysis': {
                'avg_fixture_difficulty': np.mean([p.fixture_difficulty_score for p in squad])
            },
            'differential_analysis': {
                'avg_differential_score': np.mean([p.differential_score for p in squad])
            }
        }
    
    def get_captain_recommendations(self, squad: List[PlayerScore], 
                                  num_recommendations: int = 5) -> List[PlayerScore]:
        """Get captain recommendations from the squad."""
        if not squad:
            return []
        
        # Score players for captaincy
        captain_scores = []
        for player in squad:
            # Captain scoring factors
            captain_score = (
                0.30 * player.expected_points +  # Expected points
                0.25 * player.form_score +  # Form
                0.20 * player.fixture_difficulty_score +  # Fixture difficulty
                0.15 * (1 - player.risk_factor) +  # Low risk
                0.10 * player.team_strength_score  # Team strength
            )
            
            captain_scores.append((player, captain_score))
        
        # Sort by captain score
        captain_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [player for player, _ in captain_scores[:num_recommendations]]
    
    def get_transfer_recommendations(self, current_squad: List[int], 
                                   constraints: SquadConstraints,
                                   num_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Get transfer recommendations for current squad."""
        current_players = [self.player_scores[pid] for pid in current_squad if pid in self.player_scores]
        
        if not current_players:
            return []
        
        # Find potential replacements for each position
        transfer_recommendations = []
        
        for position in [Position.GK, Position.DEF, Position.MID, Position.FWD]:
            current_position_players = [p for p in current_players if p.position == position]
            all_position_players = [p for p in self.player_scores.values() if p.position == position]
            
            # Sort current players by score (worst first)
            current_position_players.sort(key=lambda x: x.total_score)
            
            # Sort all players by score (best first)
            all_position_players.sort(key=lambda x: x.total_score, reverse=True)
            
            # Find potential upgrades
            for current_player in current_position_players[:3]:  # Consider worst 3 players
                for potential_player in all_position_players:
                    if potential_player.player_id in current_squad:
                        continue
                    
                    if potential_player.price > current_player.price + constraints.budget:
                        continue
                    
                    # Calculate upgrade value
                    upgrade_value = potential_player.total_score - current_player.total_score
                    price_difference = potential_player.price - current_player.price
                    
                    if upgrade_value > 0.1:  # Significant upgrade
                        transfer_recommendations.append({
                            'transfer_out': current_player,
                            'transfer_in': potential_player,
                            'upgrade_value': upgrade_value,
                            'price_difference': price_difference,
                            'position': position.value
                        })
                        break
        
        # Sort by upgrade value
        transfer_recommendations.sort(key=lambda x: x['upgrade_value'], reverse=True)
        
        return transfer_recommendations[:num_recommendations]
