"""
API client for Fantasy Premier League with async support and comprehensive error handling.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import requests
from asyncio_throttle import Throttler

from .config import config
from .models import (
    Player, Team, Fixture, Gameweek, PlayerGameweekPerformance, 
    ManagerTeam, FPLData, Position
)
from .exceptions import APIError, RateLimitError, ValidationError


class FPLAPIClient:
    """Fantasy Premier League API client with async support."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the API client."""
        self.config = config.api
        self.session = session
        self.throttler = Throttler(rate_limit=10, period=1)  # 10 requests per second
        
        # Headers for requests
        self.headers = {
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'application/json',
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str, retries: int = None) -> Dict[str, Any]:
        """Make an HTTP request with retry logic and rate limiting."""
        if retries is None:
            retries = self.config.MAX_RETRIES
        
        async with self.throttler:
            for attempt in range(retries + 1):
                try:
                    async with self.session.get(url, timeout=self.config.TIMEOUT) as response:
                        if response.status == 429:
                            # Rate limited
                            retry_after = int(response.headers.get('Retry-After', 60))
                            await asyncio.sleep(retry_after)
                            continue
                        
                        if response.status == 200:
                            return await response.json()
                        
                        if response.status >= 500:
                            # Server error, retry
                            if attempt < retries:
                                await asyncio.sleep(self.config.RETRY_DELAY * (2 ** attempt))
                                continue
                        
                        raise APIError(f"HTTP {response.status}: {response.reason}")
                
                except asyncio.TimeoutError:
                    if attempt < retries:
                        await asyncio.sleep(self.config.RETRY_DELAY * (2 ** attempt))
                        continue
                    raise APIError("Request timeout")
                
                except aiohttp.ClientError as e:
                    if attempt < retries:
                        await asyncio.sleep(self.config.RETRY_DELAY * (2 ** attempt))
                        continue
                    raise APIError(f"Network error: {e}")
            
            raise APIError(f"Failed after {retries} retries")
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string from API."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            return None
    
    def _map_element_type_to_position(self, element_type: int) -> Position:
        """Map element type to position enum."""
        mapping = {
            1: Position.GK,
            2: Position.DEF,
            3: Position.MID,
            4: Position.FWD
        }
        return mapping.get(element_type, Position.MID)
    
    async def get_bootstrap_static(self) -> FPLData:
        """Get all static data from the bootstrap-static endpoint."""
        url = self.config.BOOTSTRAP_STATIC_URL
        data = await self._make_request(url)
        
        # Parse players
        players = []
        for player_data in data.get('elements', []):
            try:
                player = Player(
                    id=player_data['id'],
                    first_name=player_data['first_name'],
                    second_name=player_data['second_name'],
                    web_name=player_data['web_name'],
                    element_type=player_data['element_type'],
                    team=player_data['team'],
                    position=self._map_element_type_to_position(player_data['element_type']),
                    now_cost=player_data['now_cost'],
                    cost_change_start=player_data.get('cost_change_start', 0),
                    cost_change_event=player_data.get('cost_change_event', 0),
                    cost_change_event_fall=player_data.get('cost_change_event_fall', 0),
                    form=player_data.get('form'),
                    points_per_game=player_data.get('points_per_game'),
                    total_points=player_data.get('total_points', 0),
                    goals_scored=player_data.get('goals_scored', 0),
                    assists=player_data.get('assists', 0),
                    clean_sheets=player_data.get('clean_sheets', 0),
                    goals_conceded=player_data.get('goals_conceded', 0),
                    own_goals=player_data.get('own_goals', 0),
                    penalties_saved=player_data.get('penalties_saved', 0),
                    penalties_missed=player_data.get('penalties_missed', 0),
                    yellow_cards=player_data.get('yellow_cards', 0),
                    red_cards=player_data.get('red_cards', 0),
                    saves=player_data.get('saves', 0),
                    bonus=player_data.get('bonus', 0),
                    bps=player_data.get('bps', 0),
                    influence=player_data.get('influence'),
                    creativity=player_data.get('creativity'),
                    threat=player_data.get('threat'),
                    ict_index=player_data.get('ict_index'),
                    status=player_data.get('status', 'a'),
                    news=player_data.get('news'),
                    news_added=self._parse_datetime(player_data.get('news_added')),
                    ep_this=player_data.get('ep_this'),
                    ep_next=player_data.get('ep_next'),
                    selected_by_percent=player_data.get('selected_by_percent'),
                    transfers_in=player_data.get('transfers_in', 0),
                    transfers_out=player_data.get('transfers_out', 0),
                    transfers_in_event=player_data.get('transfers_in_event', 0),
                    transfers_out_event=player_data.get('transfers_out_event', 0),
                    chance_of_playing_next_round=player_data.get('chance_of_playing_next_round'),
                    chance_of_playing_this_round=player_data.get('chance_of_playing_this_round'),
                )
                players.append(player)
            except KeyError as e:
                raise ValidationError(f"Missing required field in player data: {e}")
        
        # Parse teams
        teams = []
        for team_data in data.get('teams', []):
            try:
                team = Team(
                    id=team_data['id'],
                    name=team_data['name'],
                    short_name=team_data['short_name'],
                    code=team_data['code'],
                    strength=team_data['strength'],
                    strength_overall_home=team_data['strength_overall_home'],
                    strength_overall_away=team_data['strength_overall_away'],
                    strength_attack_home=team_data['strength_attack_home'],
                    strength_attack_away=team_data['strength_attack_away'],
                    strength_defence_home=team_data['strength_defence_home'],
                    strength_defence_away=team_data['strength_defence_away'],
                    form=team_data.get('form'),
                    position=team_data.get('position', 0),
                    played=team_data.get('played', 0),
                    win=team_data.get('win', 0),
                    draw=team_data.get('draw', 0),
                    loss=team_data.get('loss', 0),
                    points=team_data.get('points', 0),
                    goals_for=team_data.get('goals_for', 0),
                    goals_against=team_data.get('goals_against', 0),
                    unavailable=team_data.get('unavailable', False),
                    pulse_id=team_data['pulse_id'],
                )
                teams.append(team)
            except KeyError as e:
                raise ValidationError(f"Missing required field in team data: {e}")
        
        # Parse fixtures
        fixtures = []
        for fixture_data in data.get('fixtures', []):
            try:
                fixture = Fixture(
                    id=fixture_data['id'],
                    code=fixture_data['code'],
                    team_h=fixture_data['team_h'],
                    team_a=fixture_data['team_a'],
                    team_h_score=fixture_data.get('team_h_score'),
                    team_a_score=fixture_data.get('team_a_score'),
                    event=fixture_data['event'],
                    finished=fixture_data.get('finished', False),
                    minutes=fixture_data.get('minutes', 0),
                    provisional_start_time=fixture_data.get('provisional_start_time', False),
                    kickoff_time=self._parse_datetime(fixture_data.get('kickoff_time')),
                    event_name=fixture_data['event_name'],
                    is_home=fixture_data.get('is_home', False),
                    difficulty=fixture_data.get('difficulty', 0),
                )
                fixtures.append(fixture)
            except KeyError as e:
                raise ValidationError(f"Missing required field in fixture data: {e}")
        
        # Parse gameweeks
        gameweeks = []
        for event_data in data.get('events', []):
            try:
                gameweek = Gameweek(
                    id=event_data['id'],
                    name=event_data['name'],
                    deadline_time=self._parse_datetime(event_data['deadline_time']),
                    average_entry_score=event_data.get('average_entry_score', 0),
                    finished=event_data.get('finished', False),
                    data_checked=event_data.get('data_checked', False),
                    highest_scoring_entry=event_data.get('highest_scoring_entry'),
                    is_previous=event_data.get('is_previous', False),
                    is_current=event_data.get('is_current', False),
                    is_next=event_data.get('is_next', False),
                )
                gameweeks.append(gameweek)
            except KeyError as e:
                raise ValidationError(f"Missing required field in gameweek data: {e}")
        
        # Populate team names in fixtures
        team_map = {team.id: team.name for team in teams}
        for fixture in fixtures:
            fixture.team_h_name = team_map.get(fixture.team_h)
            fixture.team_a_name = team_map.get(fixture.team_a)
        
        return FPLData(
            players=players,
            teams=teams,
            fixtures=fixtures,
            gameweeks=gameweeks,
            events=gameweeks,  # Same as gameweeks
            total_players=data.get('total_players', 0),
            game_settings=data.get('game_settings', {}),
            phases=data.get('phases', []),
            element_stats=data.get('element_stats', []),
            element_types=data.get('element_types', []),
        )
    
    async def get_player_summary(self, player_id: int) -> Dict[str, Any]:
        """Get detailed player summary data."""
        url = self.config.ELEMENT_SUMMARY_URL.format(player_id=player_id)
        return await self._make_request(url)
    
    async def get_manager_team(self, entry_id: int) -> ManagerTeam:
        """Get manager team data."""
        url = self.config.ENTRY_URL.format(entry_id=entry_id)
        data = await self._make_request(url)
        
        try:
            return ManagerTeam(
                entry_id=data['entry']['id'],
                name=data['entry']['name'],
                player_first_name=data['entry']['player_first_name'],
                player_last_name=data['entry']['player_last_name'],
                player_region_name=data['entry']['player_region_name'],
                player_region_short_iso=data['entry']['player_region_short_iso'],
                summary_overall_points=data['entry'].get('summary_overall_points', 0),
                summary_overall_rank=data['entry'].get('summary_overall_rank', 0),
                summary_event_points=data['entry'].get('summary_event_points', 0),
                summary_event_rank=data['entry'].get('summary_event_rank', 0),
                joined_time=self._parse_datetime(data['entry']['joined_time']),
                started_event=data['entry']['started_event'],
                favourite_team=data['entry'].get('favourite_team'),
                player_type_id=data['entry']['player_type_id'],
                sub_rank=data['entry'].get('sub_rank'),
                rank=data['entry'].get('rank'),
                rank_sort=data['entry'].get('rank_sort'),
                total_loans_taken=data['entry'].get('total_loans_taken', 0),
                total_loans_repaid=data['entry'].get('total_loans_repaid', 0),
                total_loans_used=data['entry'].get('total_loans_used', 0),
                transfers_or_loans=data['entry'].get('transfers_or_loans', 0),
                deleted=data['entry'].get('deleted', False),
                email=data['entry'].get('email'),
                joined_seconds=data['entry'].get('joined_seconds', 0),
                kit=data['entry'].get('kit'),
                league_set=data['entry'].get('league_set', []),
                use_auto_subs=data['entry'].get('use_auto_subs', True),
                has_cup=data['entry'].get('has_cup', False),
                cup_league=data['entry'].get('cup_league'),
                cup_qualified=data['entry'].get('cup_qualified'),
                active_ship=data['entry'].get('active_ship'),
                active_chip=data['entry'].get('active_chip'),
                automatic_subs=data.get('automatic_subs', []),
                entry_history=data.get('entry_history', {}),
                picks=data.get('picks', []),
            )
        except KeyError as e:
            raise ValidationError(f"Missing required field in manager team data: {e}")
    
    async def get_manager_history(self, entry_id: int) -> Dict[str, Any]:
        """Get manager history data."""
        url = self.config.ENTRY_HISTORY_URL.format(entry_id=entry_id)
        return await self._make_request(url)
    
    async def get_manager_gameweek_picks(self, entry_id: int, gameweek: int) -> Dict[str, Any]:
        """Get manager's picks for a specific gameweek."""
        url = self.config.ENTRY_GW_URL.format(entry_id=entry_id, gw=gameweek)
        return await self._make_request(url)
    
    async def get_manager_transfers(self, entry_id: int) -> Dict[str, Any]:
        """Get manager's transfer history."""
        url = self.config.ENTRY_TRANSFERS_URL.format(entry_id=entry_id)
        return await self._make_request(url)
    
    async def get_fixtures(self) -> List[Fixture]:
        """Get all fixtures data."""
        data = await self._make_request(self.config.FIXTURES_URL)
        
        fixtures = []
        for fixture_data in data:
            try:
                fixture = Fixture(
                    id=fixture_data['id'],
                    code=fixture_data['code'],
                    team_h=fixture_data['team_h'],
                    team_a=fixture_data['team_a'],
                    team_h_score=fixture_data.get('team_h_score'),
                    team_a_score=fixture_data.get('team_a_score'),
                    event=fixture_data['event'],
                    finished=fixture_data.get('finished', False),
                    minutes=fixture_data.get('minutes', 0),
                    provisional_start_time=fixture_data.get('provisional_start_time', False),
                    kickoff_time=self._parse_datetime(fixture_data.get('kickoff_time')),
                    event_name=fixture_data['event_name'],
                    is_home=fixture_data.get('is_home', False),
                    difficulty=fixture_data.get('difficulty', 0),
                )
                fixtures.append(fixture)
            except KeyError as e:
                raise ValidationError(f"Missing required field in fixture data: {e}")
        
        return fixtures


class FPLAPIClientSync:
    """Synchronous version of the FPL API client for backward compatibility."""
    
    def __init__(self):
        """Initialize the synchronous API client."""
        self.config = config.api
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'application/json',
        })
    
    def _make_request(self, url: str, retries: int = None) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        if retries is None:
            retries = self.config.MAX_RETRIES
        
        for attempt in range(retries + 1):
            try:
                response = self.session.get(url, timeout=self.config.TIMEOUT)
                
                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    time.sleep(retry_after)
                    continue
                
                if response.status_code == 200:
                    return response.json()
                
                if response.status_code >= 500:
                    # Server error, retry
                    if attempt < retries:
                        time.sleep(self.config.RETRY_DELAY * (2 ** attempt))
                        continue
                
                raise APIError(f"HTTP {response.status_code}: {response.reason}")
            
            except requests.Timeout:
                if attempt < retries:
                    time.sleep(self.config.RETRY_DELAY * (2 ** attempt))
                    continue
                raise APIError("Request timeout")
            
            except requests.RequestException as e:
                if attempt < retries:
                    time.sleep(self.config.RETRY_DELAY * (2 ** attempt))
                    continue
                raise APIError(f"Network error: {e}")
        
        raise APIError(f"Failed after {retries} retries")
    
    def get_bootstrap_static(self) -> Dict[str, Any]:
        """Get all static data from the bootstrap-static endpoint."""
        return self._make_request(self.config.BOOTSTRAP_STATIC_URL)
    
    def get_player_summary(self, player_id: int) -> Dict[str, Any]:
        """Get detailed player summary data."""
        url = self.config.ELEMENT_SUMMARY_URL.format(player_id=player_id)
        return self._make_request(url)
    
    def get_manager_team(self, entry_id: int) -> Dict[str, Any]:
        """Get manager team data."""
        url = self.config.ENTRY_URL.format(entry_id=entry_id)
        return self._make_request(url)
    
    def get_manager_history(self, entry_id: int) -> Dict[str, Any]:
        """Get manager history data."""
        url = self.config.ENTRY_HISTORY_URL.format(entry_id=entry_id)
        return self._make_request(url)
    
    def get_manager_gameweek_picks(self, entry_id: int, gameweek: int) -> Dict[str, Any]:
        """Get manager's picks for a specific gameweek."""
        url = self.config.ENTRY_GW_URL.format(entry_id=entry_id, gw=gameweek)
        return self._make_request(url)
    
    def get_manager_transfers(self, entry_id: int) -> Dict[str, Any]:
        """Get manager's transfer history."""
        url = self.config.ENTRY_TRANSFERS_URL.format(entry_id=entry_id)
        return self._make_request(url)
    
    def get_fixtures(self) -> List[Dict[str, Any]]:
        """Get all fixtures data."""
        return self._make_request(self.config.FIXTURES_URL)
