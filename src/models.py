"""
Data models for Fantasy Premier League data using Pydantic for validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class Position(str, Enum):
    """Player positions in FPL."""
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"


class Player(BaseModel):
    """Player data model."""
    
    id: int = Field(..., description="Player ID")
    first_name: str = Field(..., description="Player first name")
    second_name: str = Field(..., description="Player last name")
    web_name: str = Field(..., description="Player web name")
    element_type: int = Field(..., description="Position ID (1=GK, 2=DEF, 3=MID, 4=FWD)")
    team: int = Field(..., description="Team ID")
    position: Position = Field(..., description="Player position")
    
    # Price information
    now_cost: int = Field(..., description="Current price in 0.1 units")
    cost_change_start: int = Field(0, description="Price change since start")
    cost_change_event: int = Field(0, description="Price change this gameweek")
    cost_change_event_fall: int = Field(0, description="Price fall this gameweek")
    
    # Form and statistics
    form: Optional[str] = Field(None, description="Form rating")
    points_per_game: Optional[str] = Field(None, description="Points per game")
    total_points: int = Field(0, description="Total points")
    goals_scored: int = Field(0, description="Goals scored")
    assists: int = Field(0, description="Assists")
    clean_sheets: int = Field(0, description="Clean sheets")
    goals_conceded: int = Field(0, description="Goals conceded")
    own_goals: int = Field(0, description="Own goals")
    penalties_saved: int = Field(0, description="Penalties saved")
    penalties_missed: int = Field(0, description="Penalties missed")
    yellow_cards: int = Field(0, description="Yellow cards")
    red_cards: int = Field(0, description="Red cards")
    saves: int = Field(0, description="Saves")
    bonus: int = Field(0, description="Bonus points")
    bps: int = Field(0, description="BPS points")
    influence: Optional[str] = Field(None, description="Influence rating")
    creativity: Optional[str] = Field(None, description="Creativity rating")
    threat: Optional[str] = Field(None, description="Threat rating")
    ict_index: Optional[str] = Field(None, description="ICT index")
    
    # Availability
    status: str = Field("a", description="Player status (a=available, u=unavailable)")
    news: Optional[str] = Field(None, description="News about player")
    news_added: Optional[datetime] = Field(None, description="When news was added")
    
    # Expected points
    ep_this: Optional[str] = Field(None, description="Expected points this gameweek")
    ep_next: Optional[str] = Field(None, description="Expected points next gameweek")
    
    # Selection
    selected_by_percent: Optional[str] = Field(None, description="Selection percentage")
    transfers_in: int = Field(0, description="Transfers in")
    transfers_out: int = Field(0, description="Transfers out")
    transfers_in_event: int = Field(0, description="Transfers in this gameweek")
    transfers_out_event: int = Field(0, description="Transfers out this gameweek")
    
    # Fixtures
    chance_of_playing_next_round: Optional[int] = Field(None, description="Chance of playing next round")
    chance_of_playing_this_round: Optional[int] = Field(None, description="Chance of playing this round")
    
    @property
    def full_name(self) -> str:
        """Get player's full name."""
        return f"{self.first_name} {self.second_name}"
    
    @property
    def price(self) -> float:
        """Get player's price in actual currency."""
        return self.now_cost / 10.0
    
    @validator('element_type')
    def validate_element_type(cls, v):
        """Validate element type and set position."""
        if v not in [1, 2, 3, 4]:
            raise ValueError("Element type must be 1, 2, 3, or 4")
        return v


class Team(BaseModel):
    """Team data model."""
    
    id: int = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    short_name: str = Field(..., description="Team short name")
    code: int = Field(..., description="Team code")
    
    # Team statistics
    strength: int = Field(..., description="Team strength")
    strength_overall_home: int = Field(..., description="Home strength")
    strength_overall_away: int = Field(..., description="Away strength")
    strength_attack_home: int = Field(..., description="Home attack strength")
    strength_attack_away: int = Field(..., description="Away attack strength")
    strength_defence_home: int = Field(..., description="Home defence strength")
    strength_defence_away: int = Field(..., description="Away defence strength")
    
    # Team form
    form: Optional[str] = Field(None, description="Team form")
    position: int = Field(0, description="League position")
    played: int = Field(0, description="Games played")
    win: int = Field(0, description="Wins")
    draw: int = Field(0, description="Draws")
    loss: int = Field(0, description="Losses")
    points: int = Field(0, description="Points")
    goals_for: int = Field(0, description="Goals for")
    goals_against: int = Field(0, description="Goals against")
    
    # Team status
    unavailable: bool = Field(False, description="Team unavailable")
    pulse_id: int = Field(..., description="Pulse ID")


class Fixture(BaseModel):
    """Fixture data model."""
    
    id: int = Field(..., description="Fixture ID")
    code: int = Field(..., description="Fixture code")
    team_h: int = Field(..., description="Home team ID")
    team_a: int = Field(..., description="Away team ID")
    team_h_score: Optional[int] = Field(None, description="Home team score")
    team_a_score: Optional[int] = Field(None, description="Away team score")
    event: int = Field(..., description="Gameweek number")
    finished: bool = Field(False, description="Fixture finished")
    minutes: int = Field(0, description="Minutes played")
    provisional_start_time: bool = Field(False, description="Provisional start time")
    kickoff_time: Optional[datetime] = Field(None, description="Kickoff time")
    event_name: str = Field(..., description="Event name")
    is_home: bool = Field(..., description="Is home fixture")
    difficulty: int = Field(..., description="Fixture difficulty")
    
    # Team names (populated after processing)
    team_h_name: Optional[str] = Field(None, description="Home team name")
    team_a_name: Optional[str] = Field(None, description="Away team name")


class Gameweek(BaseModel):
    """Gameweek data model."""
    
    id: int = Field(..., description="Gameweek ID")
    name: str = Field(..., description="Gameweek name")
    deadline_time: datetime = Field(..., description="Deadline time")
    average_entry_score: int = Field(0, description="Average entry score")
    finished: bool = Field(False, description="Gameweek finished")
    data_checked: bool = Field(False, description="Data checked")
    highest_scoring_entry: Optional[int] = Field(None, description="Highest scoring entry")
    is_previous: bool = Field(False, description="Is previous gameweek")
    is_current: bool = Field(False, description="Is current gameweek")
    is_next: bool = Field(False, description="Is next gameweek")
    fixtures: List[Fixture] = Field(default_factory=list, description="Fixtures in this gameweek")


class PlayerGameweekPerformance(BaseModel):
    """Player performance in a specific gameweek."""
    
    player_id: int = Field(..., description="Player ID")
    gameweek: int = Field(..., description="Gameweek number")
    fixture: int = Field(..., description="Fixture ID")
    team: int = Field(..., description="Team ID")
    opponent_team: int = Field(..., description="Opponent team ID")
    was_home: bool = Field(..., description="Was home fixture")
    minutes: int = Field(0, description="Minutes played")
    goals_scored: int = Field(0, description="Goals scored")
    assists: int = Field(0, description="Assists")
    clean_sheets: int = Field(0, description="Clean sheets")
    goals_conceded: int = Field(0, description="Goals conceded")
    own_goals: int = Field(0, description="Own goals")
    penalties_saved: int = Field(0, description="Penalties saved")
    penalties_missed: int = Field(0, description="Penalties missed")
    yellow_cards: int = Field(0, description="Yellow cards")
    red_cards: int = Field(0, description="Red cards")
    saves: int = Field(0, description="Saves")
    bonus: int = Field(0, description="Bonus points")
    bps: int = Field(0, description="BPS points")
    influence: str = Field("0.0", description="Influence rating")
    creativity: str = Field("0.0", description="Creativity rating")
    threat: str = Field("0.0", description="Threat rating")
    ict_index: str = Field("0.0", description="ICT index")
    total_points: int = Field(0, description="Total points")
    value: int = Field(0, description="Value at time")
    transfers_balance: int = Field(0, description="Transfer balance")
    selected: int = Field(0, description="Times selected")
    transfers_in: int = Field(0, description="Transfers in")
    transfers_out: int = Field(0, description="Transfers out")


class ManagerTeam(BaseModel):
    """Manager's team data model."""
    
    entry_id: int = Field(..., description="Entry ID")
    name: str = Field(..., description="Team name")
    player_first_name: str = Field(..., description="Manager first name")
    player_last_name: str = Field(..., description="Manager last name")
    player_region_name: str = Field(..., description="Manager region")
    player_region_short_iso: str = Field(..., description="Manager region code")
    summary_overall_points: int = Field(0, description="Overall points")
    summary_overall_rank: int = Field(0, description="Overall rank")
    summary_event_points: int = Field(0, description="Current gameweek points")
    summary_event_rank: int = Field(0, description="Current gameweek rank")
    joined_time: datetime = Field(..., description="Joined time")
    started_event: int = Field(..., description="Started event")
    favourite_team: Optional[int] = Field(None, description="Favourite team")
    player_type_id: int = Field(..., description="Player type ID")
    sub_rank: Optional[int] = Field(None, description="Sub rank")
    rank: Optional[int] = Field(None, description="Rank")
    rank_sort: Optional[int] = Field(None, description="Rank sort")
    total_loans_taken: int = Field(0, description="Total loans taken")
    total_loans_repaid: int = Field(0, description="Total loans repaid")
    total_loans_used: int = Field(0, description="Total loans used")
    transfers_or_loans: int = Field(0, description="Transfers or loans")
    deleted: bool = Field(False, description="Deleted")
    email: Optional[str] = Field(None, description="Email")
    joined_seconds: int = Field(0, description="Joined seconds")
    kit: Optional[str] = Field(None, description="Kit")
    league_set: List[int] = Field(default_factory=list, description="League set")
    use_auto_subs: bool = Field(True, description="Use auto subs")
    has_cup: bool = Field(False, description="Has cup")
    cup_league: Optional[int] = Field(None, description="Cup league")
    cup_qualified: Optional[bool] = Field(None, description="Cup qualified")
    active_ship: Optional[int] = Field(None, description="Active ship")
    active_chip: Optional[str] = Field(None, description="Active chip")
    automatic_subs: List[Dict[str, Any]] = Field(default_factory=list, description="Automatic subs")
    entry_history: Dict[str, Any] = Field(default_factory=dict, description="Entry history")
    picks: List[Dict[str, Any]] = Field(default_factory=list, description="Picks")


class FPLData(BaseModel):
    """Complete FPL data model containing all data."""
    
    players: List[Player] = Field(default_factory=list, description="All players")
    teams: List[Team] = Field(default_factory=list, description="All teams")
    fixtures: List[Fixture] = Field(default_factory=list, description="All fixtures")
    gameweeks: List[Gameweek] = Field(default_factory=list, description="All gameweeks")
    events: List[Gameweek] = Field(default_factory=list, description="Events (same as gameweeks)")
    total_players: int = Field(0, description="Total players")
    game_settings: Dict[str, Any] = Field(default_factory=dict, description="Game settings")
    phases: List[Dict[str, Any]] = Field(default_factory=list, description="Phases")
    element_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Element stats")
    element_types: List[Dict[str, Any]] = Field(default_factory=list, description="Element types")
    
    @property
    def current_gameweek(self) -> Optional[Gameweek]:
        """Get the current gameweek."""
        for gw in self.gameweeks:
            if gw.is_current:
                return gw
        return None
    
    @property
    def next_gameweek(self) -> Optional[Gameweek]:
        """Get the next gameweek."""
        for gw in self.gameweeks:
            if gw.is_next:
                return gw
        return None
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Get a player by ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get a team by ID."""
        for team in self.teams:
            if team.id == team_id:
                return team
        return None
    
    def get_fixtures_by_gameweek(self, gameweek: int) -> List[Fixture]:
        """Get all fixtures for a specific gameweek."""
        return [f for f in self.fixtures if f.event == gameweek]
    
    def get_players_by_team(self, team_id: int) -> List[Player]:
        """Get all players from a specific team."""
        return [p for p in self.players if p.team == team_id]
    
    def get_players_by_position(self, position: Position) -> List[Player]:
        """Get all players of a specific position."""
        return [p for p in self.players if p.position == position]
