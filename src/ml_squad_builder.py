"""
Advanced Machine Learning Squad Builder for Fantasy Premier League.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor

from .models import Player, Team, Fixture, Position, FPLData
from .data_processor import FPLDataProcessor
from .squad_builder import SquadBuilder, SquadConstraints, PlayerScore
from .exceptions import DataProcessingError


@dataclass
class MLPlayerScore(PlayerScore):
    """Enhanced player score with ML predictions."""
    predicted_points: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    cluster_id: int = 0
    similarity_score: float = 0.0
    market_efficiency_score: float = 0.0


class MLSquadBuilder(SquadBuilder):
    """
    Advanced squad builder using machine learning approaches.
    """
    
    def __init__(self, fpl_data: FPLData, processor: FPLDataProcessor):
        """Initialize the ML squad builder."""
        super().__init__(fpl_data, processor)
        self.ml_models = {}
        self.scalers = {}
        self.player_clusters = {}
        self._initialize_ml_models()
        self._calculate_ml_player_scores()
    
    def _initialize_ml_models(self):
        """Initialize machine learning models."""
        # Points prediction models
        self.ml_models['points_predictor'] = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'ridge_regression': Ridge(alpha=1.0),
            'lasso_regression': Lasso(alpha=0.1),
            'svr': SVR(kernel='rbf', C=1.0),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
        }
        
        # Form prediction models
        self.ml_models['form_predictor'] = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # Risk assessment models
        self.ml_models['risk_predictor'] = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # Initialize scalers
        self.scalers['features'] = StandardScaler()
        self.scalers['targets'] = MinMaxScaler()
    
    def _create_player_features(self, player: Player) -> Dict[str, float]:
        """Create comprehensive feature set for a player."""
        team = self.data.get_team_by_id(player.team)
        upcoming_fixtures = self._get_upcoming_fixtures(player.team, 5)
        
        features = {
            # Basic player stats
            'price': player.price,
            'total_points': player.total_points,
            'goals_scored': player.goals_scored,
            'assists': player.assists,
            'clean_sheets': player.clean_sheets,
            'bonus': player.bonus,
            'bps': player.bps,
            'yellow_cards': player.yellow_cards,
            'red_cards': player.red_cards,
            'saves': player.saves,
            
            # Form and performance
            'form': float(player.form) if player.form else 0.0,
            'points_per_game': float(player.points_per_game) if player.points_per_game else 0.0,
            'influence': float(player.influence) if player.influence else 0.0,
            'creativity': float(player.creativity) if player.creativity else 0.0,
            'threat': float(player.threat) if player.threat else 0.0,
            'ict_index': float(player.ict_index) if player.ict_index else 0.0,
            
            # Team performance
            'team_strength': team.strength if team else 1000,
            'team_position': team.position if team else 10,
            'team_points': team.points if team else 0,
            'team_goals_for': team.goals_for if team else 0,
            'team_goals_against': team.goals_against if team else 0,
            
            # Fixture difficulty
            'avg_fixture_difficulty': np.mean([f.difficulty for f in upcoming_fixtures]) if upcoming_fixtures else 3.0,
            'home_fixtures_ratio': sum(1 for f in upcoming_fixtures if f.team_h == player.team) / len(upcoming_fixtures) if upcoming_fixtures else 0.5,
            
            # Market indicators
            'selected_by_percent': float(player.selected_by_percent) if player.selected_by_percent else 0.0,
            'transfers_in': player.transfers_in,
            'transfers_out': player.transfers_out,
            'transfer_balance': player.transfers_in - player.transfers_out,
            
            # Expected points
            'ep_this': float(player.ep_this) if player.ep_this else 0.0,
            'ep_next': float(player.ep_next) if player.ep_next else 0.0,
            
            # Risk factors
            'chance_of_playing_next_round': player.chance_of_playing_next_round if player.chance_of_playing_next_round else 100,
            'chance_of_playing_this_round': player.chance_of_playing_this_round if player.chance_of_playing_this_round else 100,
            'has_news': 1.0 if player.news else 0.0,
            'is_available': 1.0 if player.status == 'a' else 0.0,
            
            # Position encoding
            'is_gk': 1.0 if player.position == Position.GK else 0.0,
            'is_def': 1.0 if player.position == Position.DEF else 0.0,
            'is_mid': 1.0 if player.position == Position.MID else 0.0,
            'is_fwd': 1.0 if player.position == Position.FWD else 0.0,
        }
        
        return features
    
    def _train_points_prediction_model(self):
        """Train models to predict player points."""
        # Prepare training data
        X = []
        y = []
        
        for player in self.data.players:
            if player.status != 'a' or player.total_points == 0:
                continue
            
            features = self._create_player_features(player)
            X.append(list(features.values()))
            y.append(player.total_points)
        
        if len(X) < 100:  # Need sufficient data
            return
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scalers['features'].fit_transform(X_train)
        X_test_scaled = self.scalers['features'].transform(X_test)
        
        # Train ensemble of models
        predictions = {}
        for name, model in self.ml_models['points_predictor'].items():
            try:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                predictions[name] = {'model': model, 'mse': mse, 'r2': r2}
            except Exception as e:
                print(f"Error training {name}: {e}")
        
        # Store best model
        if predictions:
            best_model_name = min(predictions.keys(), key=lambda x: predictions[x]['mse'])
            self.ml_models['best_points_predictor'] = predictions[best_model_name]['model']
    
    def _predict_player_points(self, player: Player) -> float:
        """Predict points for a player using trained models."""
        if not hasattr(self.ml_models, 'best_points_predictor'):
            return player.total_points  # Fallback to current points
        
        features = self._create_player_features(player)
        X = np.array([list(features.values())])
        X_scaled = self.scalers['features'].transform(X)
        
        try:
            predicted_points = self.ml_models['best_points_predictor'].predict(X_scaled)[0]
            return max(0.0, predicted_points)  # Ensure non-negative
        except:
            return player.total_points
    
    def _cluster_players(self):
        """Cluster players based on performance characteristics."""
        # Prepare clustering features
        clustering_features = []
        player_ids = []
        
        for player in self.data.players:
            if player.status != 'a':
                continue
            
            features = [
                player.price,
                player.total_points,
                float(player.form) if player.form else 0.0,
                float(player.points_per_game) if player.points_per_game else 0.0,
                float(player.influence) if player.influence else 0.0,
                float(player.creativity) if player.creativity else 0.0,
                float(player.threat) if player.threat else 0.0,
                player.transfers_in,
                player.transfers_out,
            ]
            
            clustering_features.append(features)
            player_ids.append(player.id)
        
        if len(clustering_features) < 10:
            return
        
        # Perform clustering
        try:
            n_clusters = min(8, len(clustering_features) // 10)  # Adaptive number of clusters
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(clustering_features)
            
            # Store cluster assignments
            for player_id, cluster_id in zip(player_ids, cluster_labels):
                self.player_clusters[player_id] = cluster_id
        except Exception as e:
            print(f"Error in clustering: {e}")
    
    def _calculate_market_efficiency_score(self, player: Player) -> float:
        """Calculate market efficiency score (how well priced the player is)."""
        if not player.points_per_game or not player.price:
            return 0.5
        
        ppg = float(player.points_per_game)
        price = player.price
        
        # Calculate expected points per million
        expected_ppm = (ppg / price) * 10
        
        # Compare with position average
        position_players = [p for p in self.data.players if p.position == player.position and p.status == 'a']
        if len(position_players) < 5:
            return 0.5
        
        avg_ppm = np.mean([(float(p.points_per_game) / p.price) * 10 for p in position_players if p.points_per_game and p.price])
        
        # Efficiency score based on comparison with average
        if avg_ppm > 0:
            efficiency = expected_ppm / avg_ppm
            return min(max(efficiency, 0.0), 2.0)  # Clamp between 0 and 2
        
        return 0.5
    
    def _calculate_similarity_score(self, player: Player) -> float:
        """Calculate similarity score based on cluster membership."""
        if player.id not in self.player_clusters:
            return 0.5
        
        cluster_id = self.player_clusters[player.id]
        cluster_members = [pid for pid, cid in self.player_clusters.items() if cid == cluster_id]
        
        # Calculate average performance of cluster members
        cluster_players = [p for p in self.data.players if p.id in cluster_members]
        if not cluster_players:
            return 0.5
        
        avg_cluster_points = np.mean([p.total_points for p in cluster_players])
        player_points = player.total_points
        
        # Similarity based on how well player performs compared to cluster average
        if avg_cluster_points > 0:
            similarity = player_points / avg_cluster_points
            return min(max(similarity, 0.0), 2.0)
        
        return 0.5
    
    def _calculate_ml_player_scores(self):
        """Calculate enhanced player scores using ML predictions."""
        # Train models
        self._train_points_prediction_model()
        self._cluster_players()
        
        # Calculate ML-enhanced scores
        for player in self.data.players:
            if player.status != 'a':
                continue
            
            # Get base scores from parent class
            base_score = self.player_scores.get(player.id)
            if not base_score:
                continue
            
            # ML predictions
            predicted_points = self._predict_player_points(player)
            market_efficiency = self._calculate_market_efficiency_score(player)
            similarity_score = self._calculate_similarity_score(player)
            cluster_id = self.player_clusters.get(player.id, 0)
            
            # Calculate confidence interval (simplified)
            confidence_lower = predicted_points * 0.8
            confidence_upper = predicted_points * 1.2
            
            # Enhanced total score incorporating ML insights
            ml_enhanced_score = (
                0.20 * base_score.total_score +  # Base score
                0.25 * (predicted_points / 100.0) +  # ML predicted points
                0.20 * market_efficiency +  # Market efficiency
                0.15 * similarity_score +  # Cluster similarity
                0.10 * base_score.form_score +  # Form
                0.10 * base_score.fixture_difficulty_score  # Fixtures
            )
            
            # Create enhanced player score
            self.player_scores[player.id] = MLPlayerScore(
                player_id=player.id,
                name=player.full_name,
                position=player.position,
                team_id=player.team,
                price=player.price,
                expected_points=base_score.expected_points,
                form_score=base_score.form_score,
                fixture_difficulty_score=base_score.fixture_difficulty_score,
                team_strength_score=base_score.team_strength_score,
                differential_score=base_score.differential_score,
                total_score=ml_enhanced_score,
                risk_factor=base_score.risk_factor,
                predicted_points=predicted_points,
                confidence_interval=(confidence_lower, confidence_upper),
                cluster_id=cluster_id,
                similarity_score=similarity_score,
                market_efficiency_score=market_efficiency
            )
    
    def build_ml_optimized_squad(self, constraints: SquadConstraints) -> Dict[str, Any]:
        """Build squad using ML-optimized approach."""
        # Get base optimal squad
        base_result = self.build_optimal_squad(constraints)
        base_squad = base_result['squad']
        
        # Apply ML-based refinements
        ml_refined_squad = self._apply_ml_refinements(base_squad, constraints)
        
        # Generate alternative strategies
        alternative_squads = self._generate_alternative_strategies(constraints)
        
        # Ensemble selection
        final_squad = self._ensemble_squad_selection([ml_refined_squad] + alternative_squads, constraints)
        
        return {
            'squad': final_squad,
            'ml_analysis': self._analyze_ml_squad(final_squad, constraints),
            'alternatives': alternative_squads,
            'base_squad': base_squad
        }
    
    def _apply_ml_refinements(self, squad: List[PlayerScore], constraints: SquadConstraints) -> List[PlayerScore]:
        """Apply ML-based refinements to the squad."""
        if not squad:
            return squad
        
        # Identify underperforming players using ML predictions
        ml_squad = [self.player_scores[p.player_id] for p in squad if p.player_id in self.player_scores]
        
        # Sort by ML-enhanced score
        ml_squad.sort(key=lambda x: x.total_score, reverse=True)
        
        # Replace worst performers with better ML-predicted alternatives
        refined_squad = []
        remaining_budget = constraints.budget
        team_counts = {}
        
        for player in ml_squad:
            if len(refined_squad) >= 15:
                break
            
            if player.price <= remaining_budget:
                if team_counts.get(player.team_id, 0) < constraints.max_players_per_team:
                    refined_squad.append(player)
                    remaining_budget -= player.price
                    team_counts[player.team_id] = team_counts.get(player.team_id, 0) + 1
        
        return refined_squad[:15]
    
    def _generate_alternative_strategies(self, constraints: SquadConstraints) -> List[List[PlayerScore]]:
        """Generate alternative squad strategies using different ML approaches."""
        strategies = []
        
        # Strategy 1: High predicted points
        high_prediction_squad = self._build_high_prediction_squad(constraints)
        strategies.append(high_prediction_squad)
        
        # Strategy 2: Market efficiency focused
        efficiency_squad = self._build_efficiency_squad(constraints)
        strategies.append(efficiency_squad)
        
        # Strategy 3: Cluster-based diversity
        cluster_squad = self._build_cluster_diverse_squad(constraints)
        strategies.append(cluster_squad)
        
        # Strategy 4: Risk-adjusted returns
        risk_adjusted_squad = self._build_risk_adjusted_squad(constraints)
        strategies.append(risk_adjusted_squad)
        
        return strategies
    
    def _build_high_prediction_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad focusing on high ML-predicted points."""
        ml_players = [p for p in self.player_scores.values() if isinstance(p, MLPlayerScore)]
        ml_players.sort(key=lambda x: x.predicted_points, reverse=True)
        
        return self._select_players_by_constraints(ml_players, constraints)
    
    def _build_efficiency_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad focusing on market efficiency."""
        ml_players = [p for p in self.player_scores.values() if isinstance(p, MLPlayerScore)]
        ml_players.sort(key=lambda x: x.market_efficiency_score, reverse=True)
        
        return self._select_players_by_constraints(ml_players, constraints)
    
    def _build_cluster_diverse_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad with diverse cluster representation."""
        ml_players = [p for p in self.player_scores.values() if isinstance(p, MLPlayerScore)]
        
        # Sort by cluster diversity and performance
        cluster_counts = {}
        for player in ml_players:
            cluster_counts[player.cluster_id] = cluster_counts.get(player.cluster_id, 0) + 1
        
        # Score based on cluster diversity and individual performance
        for player in ml_players:
            cluster_diversity = 1.0 / (cluster_counts.get(player.cluster_id, 1))
            player.total_score = (player.total_score + cluster_diversity) / 2.0
        
        ml_players.sort(key=lambda x: x.total_score, reverse=True)
        return self._select_players_by_constraints(ml_players, constraints)
    
    def _build_risk_adjusted_squad(self, constraints: SquadConstraints) -> List[PlayerScore]:
        """Build squad with risk-adjusted returns."""
        ml_players = [p for p in self.player_scores.values() if isinstance(p, MLPlayerScore)]
        
        # Calculate risk-adjusted returns
        for player in ml_players:
            risk_adjusted_return = player.predicted_points / (1 + player.risk_factor)
            player.total_score = risk_adjusted_return / 100.0  # Normalize
        
        ml_players.sort(key=lambda x: x.total_score, reverse=True)
        return self._select_players_by_constraints(ml_players, constraints)
    
    def _ensemble_squad_selection(self, squads: List[List[PlayerScore]], 
                                 constraints: SquadConstraints) -> List[PlayerScore]:
        """Use ensemble methods to select the best squad."""
        if not squads:
            return []
        
        # Score each squad using multiple metrics
        squad_scores = []
        
        for squad in squads:
            if len(squad) != 15:
                continue
            
            # Calculate ensemble score
            total_cost = sum(p.price for p in squad)
            total_predicted_points = sum(p.predicted_points for p in squad if isinstance(p, MLPlayerScore))
            avg_efficiency = np.mean([p.market_efficiency_score for p in squad if isinstance(p, MLPlayerScore)])
            cluster_diversity = len(set(p.cluster_id for p in squad if isinstance(p, MLPlayerScore)))
            avg_risk = np.mean([p.risk_factor for p in squad])
            
            ensemble_score = (
                0.30 * (total_predicted_points / 15.0) +  # Predicted points
                0.25 * avg_efficiency +  # Market efficiency
                0.20 * (cluster_diversity / 8.0) +  # Cluster diversity
                0.15 * (1 - avg_risk) +  # Risk factor
                0.10 * (1.0 if total_cost <= constraints.budget else 0.5)  # Budget compliance
            )
            
            squad_scores.append((squad, ensemble_score))
        
        # Return the best squad
        if squad_scores:
            best_squad = max(squad_scores, key=lambda x: x[1])
            return best_squad[0]
        
        return squads[0] if squads else []
    
    def _analyze_ml_squad(self, squad: List[PlayerScore], constraints: SquadConstraints) -> Dict[str, Any]:
        """Analyze the ML-optimized squad."""
        if not squad:
            return {}
        
        base_analysis = self._analyze_squad(squad, constraints)
        
        # ML-specific analysis
        ml_players = [p for p in squad if isinstance(p, MLPlayerScore)]
        
        if not ml_players:
            return base_analysis
        
        ml_analysis = {
            'total_predicted_points': sum(p.predicted_points for p in ml_players),
            'avg_predicted_points': np.mean([p.predicted_points for p in ml_players]),
            'avg_market_efficiency': np.mean([p.market_efficiency_score for p in ml_players]),
            'cluster_distribution': {},
            'confidence_intervals': {
                'avg_lower': np.mean([p.confidence_interval[0] for p in ml_players]),
                'avg_upper': np.mean([p.confidence_interval[1] for p in ml_players])
            },
            'similarity_analysis': {
                'avg_similarity': np.mean([p.similarity_score for p in ml_players]),
                'high_similarity_players': len([p for p in ml_players if p.similarity_score > 1.2])
            }
        }
        
        # Cluster distribution
        for player in ml_players:
            cluster_id = player.cluster_id
            ml_analysis['cluster_distribution'][f'cluster_{cluster_id}'] = \
                ml_analysis['cluster_distribution'].get(f'cluster_{cluster_id}', 0) + 1
        
        return {**base_analysis, 'ml_analysis': ml_analysis}
    
    def get_ml_transfer_recommendations(self, current_squad: List[int], 
                                      constraints: SquadConstraints,
                                      num_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Get ML-enhanced transfer recommendations."""
        current_players = [self.player_scores[pid] for pid in current_squad if pid in self.player_scores]
        
        if not current_players:
            return []
        
        transfer_recommendations = []
        
        for position in [Position.GK, Position.DEF, Position.MID, Position.FWD]:
            current_position_players = [p for p in current_players if p.position == position]
            all_position_players = [p for p in self.player_scores.values() if p.position == position and isinstance(p, MLPlayerScore)]
            
            # Sort by ML-enhanced metrics
            current_position_players.sort(key=lambda x: x.total_score)
            all_position_players.sort(key=lambda x: x.predicted_points, reverse=True)
            
            for current_player in current_position_players[:3]:
                for potential_player in all_position_players:
                    if potential_player.player_id in current_squad:
                        continue
                    
                    if potential_player.price > current_player.price + constraints.budget:
                        continue
                    
                    # ML-enhanced upgrade calculation
                    points_upgrade = potential_player.predicted_points - current_player.predicted_points
                    efficiency_upgrade = potential_player.market_efficiency_score - current_player.market_efficiency_score
                    
                    upgrade_value = (points_upgrade / 10.0) + (efficiency_upgrade * 0.5)
                    
                    if upgrade_value > 0.05:  # Significant upgrade
                        transfer_recommendations.append({
                            'transfer_out': current_player,
                            'transfer_in': potential_player,
                            'upgrade_value': upgrade_value,
                            'points_upgrade': points_upgrade,
                            'efficiency_upgrade': efficiency_upgrade,
                            'price_difference': potential_player.price - current_player.price,
                            'position': position.value,
                            'confidence': potential_player.confidence_interval
                        })
                        break
        
        # Sort by upgrade value
        transfer_recommendations.sort(key=lambda x: x['upgrade_value'], reverse=True)
        
        return transfer_recommendations[:num_recommendations]
