"""
Data processing and analysis utilities for FPL data.
"""

import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from .models import (
    Player, Team, Fixture, Gameweek, PlayerGameweekPerformance, 
    FPLData, Position
)
from .exceptions import DataProcessingError


class FPLDataProcessor:
    """Data processor for analyzing and processing FPL data."""
    
    def __init__(self, fpl_data: FPLData):
        """Initialize the data processor with FPL data."""
        self.data = fpl_data
        self._create_dataframes()
    
    def _create_dataframes(self):
        """Create pandas DataFrames from the FPL data."""
        # Convert players to DataFrame
        self.players_df = pd.DataFrame([
            {
                'id': p.id,
                'name': p.full_name,
                'web_name': p.web_name,
                'position': p.position.value,
                'team_id': p.team,
                'team_name': self.data.get_team_by_id(p.team).name if self.data.get_team_by_id(p.team) else None,
                'price': p.price,
                'form': float(p.form) if p.form else None,
                'points_per_game': float(p.points_per_game) if p.points_per_game else None,
                'total_points': p.total_points,
                'goals_scored': p.goals_scored,
                'assists': p.assists,
                'clean_sheets': p.clean_sheets,
                'goals_conceded': p.goals_conceded,
                'bonus': p.bonus,
                'bps': p.bps,
                'influence': float(p.influence) if p.influence else None,
                'creativity': float(p.creativity) if p.creativity else None,
                'threat': float(p.threat) if p.threat else None,
                'ict_index': float(p.ict_index) if p.ict_index else None,
                'selected_by_percent': float(p.selected_by_percent) if p.selected_by_percent else None,
                'transfers_in': p.transfers_in,
                'transfers_out': p.transfers_out,
                'ep_this': float(p.ep_this) if p.ep_this else None,
                'ep_next': float(p.ep_next) if p.ep_next else None,
                'status': p.status,
                'news': p.news,
                'chance_of_playing_next_round': p.chance_of_playing_next_round,
                'chance_of_playing_this_round': p.chance_of_playing_this_round,
            }
            for p in self.data.players
        ])
        
        # Convert teams to DataFrame
        self.teams_df = pd.DataFrame([
            {
                'id': t.id,
                'name': t.name,
                'short_name': t.short_name,
                'strength': t.strength,
                'strength_overall_home': t.strength_overall_home,
                'strength_overall_away': t.strength_overall_away,
                'strength_attack_home': t.strength_attack_home,
                'strength_attack_away': t.strength_attack_away,
                'strength_defence_home': t.strength_defence_home,
                'strength_defence_away': t.strength_defence_away,
                'form': t.form,
                'position': t.position,
                'played': t.played,
                'win': t.win,
                'draw': t.draw,
                'loss': t.loss,
                'points': t.points,
                'goals_for': t.goals_for,
                'goals_against': t.goals_against,
            }
            for t in self.data.teams
        ])
        
        # Convert fixtures to DataFrame
        self.fixtures_df = pd.DataFrame([
            {
                'id': f.id,
                'team_h': f.team_h,
                'team_h_name': f.team_h_name,
                'team_a': f.team_a,
                'team_a_name': f.team_a_name,
                'team_h_score': f.team_h_score,
                'team_a_score': f.team_a_score,
                'event': f.event,
                'finished': f.finished,
                'kickoff_time': f.kickoff_time,
                'difficulty': f.difficulty,
            }
            for f in self.data.fixtures
        ])
    
    def get_players_by_position(self, position: Position) -> pd.DataFrame:
        """Get players filtered by position."""
        return self.players_df[self.players_df['position'] == position.value]
    
    def get_players_by_team(self, team_id: int) -> pd.DataFrame:
        """Get players filtered by team."""
        return self.players_df[self.players_df['team_id'] == team_id]
    
    def get_top_performers(self, position: Optional[Position] = None, 
                          metric: str = 'total_points', top_n: int = 10) -> pd.DataFrame:
        """Get top performing players by a specific metric."""
        df = self.players_df.copy()
        
        if position:
            df = df[df['position'] == position.value]
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', metric, 'price', 'form', 'points_per_game', 
                  'goals_scored', 'assists', 'clean_sheets', 'bonus', 'selected_by_percent', 
                  'transfers_in', 'transfers_out', 'ep_this', 'ep_next', 'status', 'news', 
                  'chance_of_playing_next_round']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in df.columns]
        
        return df.nlargest(top_n, metric)[available_columns]
    
    def get_value_players(self, position: Optional[Position] = None, 
                         min_points: int = 50, top_n: int = 10) -> pd.DataFrame:
        """Get players with best value (points per million)."""
        df = self.players_df.copy()
        
        if position:
            df = df[df['position'] == position.value]
        
        # Filter by minimum points
        df = df[df['total_points'] >= min_points]
        
        # Calculate points per million
        df['points_per_million'] = (df['total_points'] / df['price']) * 10
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', 'total_points', 'price', 'points_per_million',
                  'form', 'points_per_game', 'goals_scored', 'assists', 'clean_sheets', 'bonus', 
                  'selected_by_percent', 'transfers_in', 'transfers_out', 'ep_this', 'ep_next', 
                  'status', 'news', 'chance_of_playing_next_round']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in df.columns]
        
        return df.nlargest(top_n, 'points_per_million')[available_columns]
    
    def get_form_players(self, position: Optional[Position] = None, 
                        min_form: float = 5.0, top_n: int = 10) -> pd.DataFrame:
        """Get players with good form."""
        df = self.players_df.copy()
        
        if position:
            df = df[df['position'] == position.value]
        
        # Filter by minimum form
        df = df[df['form'] >= min_form]
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', 'form', 'price', 'total_points', 
                  'points_per_game', 'goals_scored', 'assists', 'clean_sheets', 'bonus', 
                  'selected_by_percent', 'transfers_in', 'transfers_out', 'ep_this', 'ep_next', 
                  'status', 'news', 'chance_of_playing_next_round']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in df.columns]
        
        return df.nlargest(top_n, 'form')[available_columns]
    
    def get_fixture_difficulty_analysis(self, gameweeks: List[int] = None) -> pd.DataFrame:
        """Analyze fixture difficulty for upcoming gameweeks."""
        if gameweeks is None:
            # Get next 5 gameweeks
            current_gw = self.data.current_gameweek
            if current_gw:
                gameweeks = list(range(current_gw.id + 1, min(current_gw.id + 6, 39)))
            else:
                gameweeks = list(range(1, 6))
        
        fixture_analysis = []
        
        for gw in gameweeks:
            gw_fixtures = self.fixtures_df[self.fixtures_df['event'] == gw]
            
            for _, fixture in gw_fixtures.iterrows():
                # Home team analysis
                home_team = self.teams_df[self.teams_df['id'] == fixture['team_h']].iloc[0]
                home_players = self.get_players_by_team(fixture['team_h'])
                
                fixture_analysis.append({
                    'gameweek': gw,
                    'team_id': fixture['team_h'],
                    'team_name': fixture['team_h_name'],
                    'opponent_id': fixture['team_a'],
                    'opponent_name': fixture['team_a_name'],
                    'is_home': True,
                    'difficulty': fixture['difficulty'],
                    'team_strength': home_team['strength'],
                    'attack_strength': home_team['strength_attack_home'],
                    'defence_strength': home_team['strength_defence_home'],
                    'avg_player_points': home_players['total_points'].mean() if not home_players.empty else 0,
                    'top_performer': home_players.loc[home_players['total_points'].idxmax(), 'name'] if not home_players.empty else None,
                })
                
                # Away team analysis
                away_team = self.teams_df[self.teams_df['id'] == fixture['team_a']].iloc[0]
                away_players = self.get_players_by_team(fixture['team_a'])
                
                fixture_analysis.append({
                    'gameweek': gw,
                    'team_id': fixture['team_a'],
                    'team_name': fixture['team_a_name'],
                    'opponent_id': fixture['team_h'],
                    'opponent_name': fixture['team_h_name'],
                    'is_home': False,
                    'difficulty': fixture['difficulty'],
                    'team_strength': away_team['strength'],
                    'attack_strength': away_team['strength_attack_away'],
                    'defence_strength': away_team['strength_defence_away'],
                    'avg_player_points': away_players['total_points'].mean() if not away_players.empty else 0,
                    'top_performer': away_players.loc[away_players['total_points'].idxmax(), 'name'] if not away_players.empty else None,
                })
        
        return pd.DataFrame(fixture_analysis)
    
    def get_team_analysis(self) -> pd.DataFrame:
        """Get comprehensive team analysis."""
        team_analysis = []
        
        for _, team in self.teams_df.iterrows():
            players = self.get_players_by_team(team['id'])
            
            if not players.empty:
                analysis = {
                    'team_id': team['id'],
                    'team_name': team['name'],
                    'league_position': team['position'],
                    'points': team['points'],
                    'goals_for': team['goals_for'],
                    'goals_against': team['goals_against'],
                    'goal_difference': team['goals_for'] - team['goals_against'],
                    'total_players': len(players),
                    'avg_player_points': players['total_points'].mean(),
                    'total_team_points': players['total_points'].sum(),
                    'avg_player_price': players['price'].mean(),
                    'total_team_value': players['price'].sum(),
                    'top_scorer': players.loc[players['total_points'].idxmax(), 'name'],
                    'top_scorer_points': players['total_points'].max(),
                    'most_expensive': players.loc[players['price'].idxmax(), 'name'],
                    'most_expensive_price': players['price'].max(),
                    'gk_count': len(players[players['position'] == Position.GK.value]),
                    'def_count': len(players[players['position'] == Position.DEF.value]),
                    'mid_count': len(players[players['position'] == Position.MID.value]),
                    'fwd_count': len(players[players['position'] == Position.FWD.value]),
                }
                team_analysis.append(analysis)
        
        return pd.DataFrame(team_analysis)
    
    def get_position_analysis(self) -> Dict[str, pd.DataFrame]:
        """Get analysis by position."""
        analysis = {}
        
        for position in Position:
            players = self.get_players_by_position(position)
            
            if not players.empty:
                analysis[position.value] = {
                    'count': len(players),
                    'avg_points': players['total_points'].mean(),
                    'avg_price': players['price'].mean(),
                    'avg_form': players['form'].mean(),
                    'top_performer': players.loc[players['total_points'].idxmax(), 'name'],
                    'most_expensive': players.loc[players['price'].idxmax(), 'name'],
                    'best_value': players.loc[(players['total_points'] / players['price']).idxmax(), 'name'],
                }
        
        return analysis
    
    def get_transfer_targets(self, position: Optional[Position] = None, 
                           min_transfers_in: int = 1000) -> pd.DataFrame:
        """Get players with high transfer activity."""
        df = self.players_df.copy()
        
        if position:
            df = df[df['position'] == position.value]
        
        # Filter by minimum transfers in
        df = df[df['transfers_in'] >= min_transfers_in]
        
        # Calculate transfer balance
        df['transfer_balance'] = df['transfers_in'] - df['transfers_out']
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', 'transfers_in', 'transfers_out', 
                  'transfer_balance', 'price', 'total_points', 'form', 'points_per_game', 
                  'goals_scored', 'assists', 'clean_sheets', 'bonus', 'selected_by_percent', 
                  'ep_this', 'ep_next', 'status', 'news', 'chance_of_playing_next_round']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in df.columns]
        
        return df.nlargest(20, 'transfer_balance')[available_columns]
    
    def get_differential_players(self, position: Optional[Position] = None, 
                               max_selection: float = 5.0, min_points: int = 50) -> pd.DataFrame:
        """Get differential players (low ownership, good performance)."""
        df = self.players_df.copy()
        
        if position:
            df = df[df['position'] == position.value]
        
        # Filter by selection percentage and minimum points
        df = df[(df['selected_by_percent'] <= max_selection) & (df['total_points'] >= min_points)]
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', 'selected_by_percent', 'total_points', 
                  'price', 'form', 'points_per_game', 'goals_scored', 'assists', 'clean_sheets', 
                  'bonus', 'transfers_in', 'transfers_out', 'ep_this', 'ep_next', 'status', 
                  'news', 'chance_of_playing_next_round']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in df.columns]
        
        return df.nlargest(20, 'total_points')[available_columns]
    
    def get_injury_concerns(self) -> pd.DataFrame:
        """Get players with injury concerns or availability issues."""
        df = self.players_df.copy()
        
        # Filter for players with issues
        injury_players = df[
            (df['status'] != 'a') |  # Not available
            (df['news'].notna()) |   # Has news
            (df['chance_of_playing_next_round'] < 100) |  # Less than 100% chance
            (df['chance_of_playing_this_round'] < 100)    # Less than 100% chance
        ]
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', 'status', 'news', 
                  'chance_of_playing_next_round', 'chance_of_playing_this_round', 'price',
                  'total_points', 'form', 'points_per_game', 'goals_scored', 'assists', 
                  'clean_sheets', 'bonus', 'selected_by_percent', 'transfers_in', 
                  'transfers_out', 'ep_this', 'ep_next']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in injury_players.columns]
        
        return injury_players[available_columns].sort_values('chance_of_playing_next_round', ascending=True)
    
    def get_expected_points_analysis(self) -> pd.DataFrame:
        """Get players with high expected points."""
        df = self.players_df.copy()
        
        # Filter for players with expected points
        df = df[df['ep_this'].notna()]
        
        # Include all necessary columns for API responses
        columns = ['id', 'name', 'team_name', 'position', 'ep_this', 'ep_next', 'price', 
                  'total_points', 'form', 'points_per_game', 'goals_scored', 'assists', 
                  'clean_sheets', 'bonus', 'selected_by_percent', 'transfers_in', 
                  'transfers_out', 'status', 'news', 'chance_of_playing_next_round']
        
        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns if col in df.columns]
        
        return df.nlargest(20, 'ep_this')[available_columns]
    
    def export_to_csv(self, filename: str, data: pd.DataFrame):
        """Export data to CSV file."""
        try:
            data.to_csv(filename, index=False)
        except Exception as e:
            raise DataProcessingError(f"Failed to export data to CSV: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of the FPL data."""
        return {
            'total_players': len(self.data.players),
            'total_teams': len(self.data.teams),
            'total_fixtures': len(self.data.fixtures),
            'current_gameweek': self.data.current_gameweek.id if self.data.current_gameweek else None,
            'next_gameweek': self.data.next_gameweek.id if self.data.next_gameweek else None,
            'avg_player_price': self.players_df['price'].mean(),
            'avg_player_points': self.players_df['total_points'].mean(),
            'total_team_value': self.players_df['price'].sum(),
            'position_distribution': self.players_df['position'].value_counts().to_dict(),
            'team_with_most_points': self.teams_df.loc[self.teams_df['points'].idxmax(), 'name'],
            'player_with_most_points': self.players_df.loc[self.players_df['total_points'].idxmax(), 'name'],
            'most_expensive_player': self.players_df.loc[self.players_df['price'].idxmax(), 'name'],
        }
