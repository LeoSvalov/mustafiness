"""
FastAPI service for FPL Data Collector.

This module provides a RESTful API wrapper around the FPL data collector,
allowing it to be run as an independent service with all necessary endpoints.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .collector import FPLDataCollector
from .models import Position, Player, Team, Fixture, Gameweek
from .exceptions import FPLException, APIError, ValidationError, DataProcessingError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "2.0.0"


class DataCollectionResponse(BaseModel):
    status: str
    message: str
    total_players: Optional[int] = None
    total_teams: Optional[int] = None
    total_fixtures: Optional[int] = None
    current_gameweek: Optional[int] = None
    next_gameweek: Optional[int] = None


class PlayerResponse(BaseModel):
    id: int
    name: str
    team_name: str
    position: str
    price: float
    total_points: int
    form: Optional[float] = None
    points_per_game: Optional[float] = None
    goals_scored: int
    assists: int
    clean_sheets: int
    bonus: int
    selected_by_percent: Optional[float] = None
    transfers_in: int
    transfers_out: int
    ep_this: Optional[float] = None
    ep_next: Optional[float] = None
    status: str
    news: Optional[str] = None
    # chance_of_playing_next_round: Optional[int] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: str
    strength: int
    position: int
    points: int
    goals_for: int
    goals_against: int
    form: Optional[str] = None


class FixtureResponse(BaseModel):
    id: int
    team_h_name: str
    team_a_name: str
    event: int
    difficulty: int
    finished: bool
    kickoff_time: Optional[datetime] = None
    team_h_score: Optional[int] = None
    team_a_score: Optional[int] = None


class GameweekResponse(BaseModel):
    id: int
    name: str
    deadline_time: datetime
    finished: bool
    is_current: bool
    is_next: bool


class AnalysisResponse(BaseModel):
    players: List[PlayerResponse]
    total_count: int


class FixtureAnalysisResponse(BaseModel):
    gameweek: int
    team_name: str
    opponent_name: str
    difficulty: int
    is_home: bool
    team_strength: int
    attack_strength: int
    defence_strength: int


class SummaryStatsResponse(BaseModel):
    total_players: int
    total_teams: int
    total_fixtures: int
    current_gameweek: Optional[int]
    next_gameweek: Optional[int]
    avg_player_price: float
    avg_player_points: float
    position_distribution: Dict[str, int]
    team_with_most_points: str
    player_with_most_points: str
    most_expensive_player: str


# Global collector instance
collector: Optional[FPLDataCollector] = None


def get_collector() -> FPLDataCollector:
    """Get or create the global collector instance."""
    global collector
    if collector is None:
        collector = FPLDataCollector(use_async=True, cache_data=True)
    return collector


# Create FastAPI app
app = FastAPI(
    title="FPL Data Collector API",
    description="A comprehensive API for Fantasy Premier League data collection and analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize the collector on startup."""
    global collector
    collector = FPLDataCollector(use_async=True, cache_data=True)
    logger.info("FPL Data Collector API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("FPL Data Collector API shutting down")


# Health and status endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health status."""
    return HealthResponse()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.get("/status")
async def status():
    """Get API status and data availability."""
    try:
        collector = get_collector()
        if collector.fpl_data:
            stats = collector.get_summary_stats()
            return {
                "status": "ready",
                "data_available": True,
                "last_updated": datetime.now().isoformat(),
                "summary": stats
            }
        else:
            return {
                "status": "no_data",
                "data_available": False,
                "message": "No data collected yet. Use /collect endpoint to fetch data."
            }
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return {
            "status": "error",
            "data_available": False,
            "error": str(e)
        }


# Data collection endpoints
@app.post("/collect", response_model=DataCollectionResponse)
async def collect_data(
    background_tasks: BackgroundTasks,
    force_refresh: bool = Query(False, description="Force refresh cached data")
):
    """Collect all FPL data."""
    try:
        collector = get_collector()
        
        # Run collection in background if it's a large operation
        if force_refresh:
            background_tasks.add_task(collector.collect_all_data, force_refresh=True)
            return DataCollectionResponse(
                status="started",
                message="Data collection started in background. Check /status for updates."
            )
        
        # Run synchronously for immediate response
        await collector.collect_all_data(force_refresh=force_refresh)
        
        stats = collector.get_summary_stats()
        return DataCollectionResponse(
            status="completed",
            message="Data collection completed successfully",
            total_players=stats['total_players'],
            total_teams=stats['total_teams'],
            total_fixtures=stats['total_fixtures'],
            current_gameweek=stats['current_gameweek'],
            next_gameweek=stats['next_gameweek']
        )
    
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        raise HTTPException(status_code=500, detail=f"Error collecting data: {str(e)}")


@app.post("/collect/background")
async def collect_data_background(force_refresh: bool = Query(False)):
    """Start data collection in background."""
    try:
        collector = get_collector()
        asyncio.create_task(collector.collect_all_data(force_refresh=force_refresh))
        return {"status": "started", "message": "Data collection started in background"}
    except Exception as e:
        logger.error(f"Error starting background collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Data retrieval endpoints
@app.get("/players", response_model=List[PlayerResponse])
async def get_players(
    position: Optional[str] = Query(None, description="Filter by position (GK, DEF, MID, FWD)"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    limit: int = Query(100, description="Maximum number of players to return")
):
    """Get players with optional filtering."""
    try:
        collector = get_collector()
        if not collector.fpl_data:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        players = collector.get_players(position=position, team_id=team_id)
        
        # Convert to response format
        response_players = []
        for player in players[:limit]:
            team = collector.get_team_by_id(player.team)
            response_players.append(PlayerResponse(
                id=player.id,
                name=player.full_name,
                team_name=team.name if team else "Unknown",
                position=player.position.value,
                price=player.price,
                total_points=player.total_points,
                form=float(player.form) if player.form else None,
                points_per_game=float(player.points_per_game) if player.points_per_game else None,
                goals_scored=player.goals_scored,
                assists=player.assists,
                clean_sheets=player.clean_sheets,
                bonus=player.bonus,
                selected_by_percent=float(player.selected_by_percent) if player.selected_by_percent else None,
                transfers_in=player.transfers_in,
                transfers_out=player.transfers_out,
                ep_this=float(player.ep_this) if player.ep_this else None,
                ep_next=float(player.ep_next) if player.ep_next else None,
                status=player.status,
                news=player.news,
                chance_of_playing_next_round=player.chance_of_playing_next_round
            ))
        
        return response_players
    
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teams", response_model=List[TeamResponse])
async def get_teams():
    """Get all teams."""
    try:
        collector = get_collector()
        if not collector.fpl_data:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        teams = collector.get_teams()
        return [
            TeamResponse(
                id=team.id,
                name=team.name,
                short_name=team.short_name,
                strength=team.strength,
                position=team.position,
                points=team.points,
                goals_for=team.goals_for,
                goals_against=team.goals_against,
                form=team.form
            )
            for team in teams
        ]
    
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fixtures", response_model=List[FixtureResponse])
async def get_fixtures(
    gameweek: Optional[int] = Query(None, description="Filter by gameweek"),
    limit: int = Query(100, description="Maximum number of fixtures to return")
):
    """Get fixtures with optional gameweek filtering."""
    try:
        collector = get_collector()
        if not collector.fpl_data:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        fixtures = collector.get_fixtures(gameweek=gameweek)
        return [
            FixtureResponse(
                id=fixture.id,
                team_h_name=fixture.team_h_name or "Unknown",
                team_a_name=fixture.team_a_name or "Unknown",
                event=fixture.event,
                difficulty=fixture.difficulty,
                finished=fixture.finished,
                kickoff_time=fixture.kickoff_time,
                team_h_score=fixture.team_h_score,
                team_a_score=fixture.team_a_score
            )
            for fixture in fixtures[:limit]
        ]
    
    except Exception as e:
        logger.error(f"Error getting fixtures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gameweeks", response_model=List[GameweekResponse])
async def get_gameweeks():
    """Get all gameweeks."""
    try:
        collector = get_collector()
        if not collector.fpl_data:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        gameweeks = collector.get_gameweeks()
        return [
            GameweekResponse(
                id=gw.id,
                name=gw.name,
                deadline_time=gw.deadline_time,
                finished=gw.finished,
                is_current=gw.is_current,
                is_next=gw.is_next
            )
            for gw in gameweeks
        ]
    
    except Exception as e:
        logger.error(f"Error getting gameweeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current-gameweek", response_model=GameweekResponse)
async def get_current_gameweek():
    """Get current gameweek."""
    try:
        collector = get_collector()
        if not collector.fpl_data:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        current_gw = collector.get_current_gameweek()
        if not current_gw:
            raise HTTPException(status_code=404, detail="No current gameweek found.")
        
        return GameweekResponse(
            id=current_gw.id,
            name=current_gw.name,
            deadline_time=current_gw.deadline_time,
            finished=current_gw.finished,
            is_current=current_gw.is_current,
            is_next=current_gw.is_next
        )
    
    except Exception as e:
        logger.error(f"Error getting current gameweek: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analysis endpoints
@app.get("/analysis/top-performers", response_model=AnalysisResponse)
async def get_top_performers(
    position: Optional[str] = Query(None, description="Filter by position"),
    metric: str = Query("total_points", description="Metric to sort by"),
    limit: int = Query(10, description="Number of players to return")
):
    """Get top performing players."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        pos_enum = None
        if position:
            try:
                pos_enum = Position(position.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players_df = collector.processor.get_top_performers(
            position=pos_enum,
            metric=metric,
            top_n=limit
        )
        
        players = []
        for _, player in players_df.iterrows():
            players.append(PlayerResponse(
                id=player['id'],
                name=player['name'],
                team_name=player['team_name'],
                position=player['position'],
                price=player['price'],
                total_points=player['total_points'],
                form=player.get('form'),
                points_per_game=player.get('points_per_game'),
                goals_scored=player.get('goals_scored', 0),
                assists=player.get('assists', 0),
                clean_sheets=player.get('clean_sheets', 0),
                bonus=player.get('bonus', 0),
                selected_by_percent=player.get('selected_by_percent'),
                transfers_in=player.get('transfers_in', 0),
                transfers_out=player.get('transfers_out', 0),
                ep_this=player.get('ep_this'),
                ep_next=player.get('ep_next'),
                status=player.get('status', 'a'),
                news=player.get('news'),
                # chance_of_playing_next_round=player.get('chance_of_playing_next_round')
            ))
        
        return AnalysisResponse(players=players, total_count=len(players))
    
    except Exception as e:
        logger.error(f"Error getting top performers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/value-players", response_model=AnalysisResponse)
async def get_value_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    min_points: int = Query(50, description="Minimum points required"),
    limit: int = Query(10, description="Number of players to return")
):
    """Get players with best value (points per million)."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        pos_enum = None
        if position:
            try:
                pos_enum = Position(position.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players_df = collector.processor.get_value_players(
            position=pos_enum,
            min_points=min_points,
            top_n=limit
        )
        
        players = []
        for _, player in players_df.iterrows():
            players.append(PlayerResponse(
                id=player['id'],
                name=player['name'],
                team_name=player['team_name'],
                position=player['position'],
                price=player['price'],
                total_points=player['total_points'],
                form=player.get('form'),
                points_per_game=player.get('points_per_game'),
                goals_scored=player.get('goals_scored', 0),
                assists=player.get('assists', 0),
                clean_sheets=player.get('clean_sheets', 0),
                bonus=player.get('bonus', 0),
                selected_by_percent=player.get('selected_by_percent'),
                transfers_in=player.get('transfers_in', 0),
                transfers_out=player.get('transfers_out', 0),
                ep_this=player.get('ep_this'),
                ep_next=player.get('ep_next'),
                status=player.get('status', 'a'),
                news=player.get('news'),
                chance_of_playing_next_round=player.get('chance_of_playing_next_round')
            ))
        
        return AnalysisResponse(players=players, total_count=len(players))
    
    except Exception as e:
        logger.error(f"Error getting value players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/form-players", response_model=AnalysisResponse)
async def get_form_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    min_form: float = Query(5.0, description="Minimum form required"),
    limit: int = Query(10, description="Number of players to return")
):
    """Get players with good form."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        pos_enum = None
        if position:
            try:
                pos_enum = Position(position.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players_df = collector.processor.get_form_players(
            position=pos_enum,
            min_form=min_form,
            top_n=limit
        )
        
        players = []
        for _, player in players_df.iterrows():
            players.append(PlayerResponse(
                id=player['id'],
                name=player['name'],
                team_name=player['team_name'],
                position=player['position'],
                price=player['price'],
                total_points=player['total_points'],
                form=player.get('form'),
                points_per_game=player.get('points_per_game'),
                goals_scored=player.get('goals_scored', 0),
                assists=player.get('assists', 0),
                clean_sheets=player.get('clean_sheets', 0),
                bonus=player.get('bonus', 0),
                selected_by_percent=player.get('selected_by_percent'),
                transfers_in=player.get('transfers_in', 0),
                transfers_out=player.get('transfers_out', 0),
                ep_this=player.get('ep_this'),
                ep_next=player.get('ep_next'),
                status=player.get('status', 'a'),
                news=player.get('news'),
                chance_of_playing_next_round=player.get('chance_of_playing_next_round')
            ))
        
        return AnalysisResponse(players=players, total_count=len(players))
    
    except Exception as e:
        logger.error(f"Error getting form players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/transfer-targets", response_model=AnalysisResponse)
async def get_transfer_targets(
    position: Optional[str] = Query(None, description="Filter by position"),
    min_transfers: int = Query(1000, description="Minimum transfers in required"),
    limit: int = Query(10, description="Number of players to return")
):
    """Get players with high transfer activity."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        pos_enum = None
        if position:
            try:
                pos_enum = Position(position.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players_df = collector.processor.get_transfer_targets(
            position=pos_enum,
            min_transfers_in=min_transfers,
            top_n=limit
        )
        
        players = []
        for _, player in players_df.iterrows():
            players.append(PlayerResponse(
                id=player['id'],
                name=player['name'],
                team_name=player['team_name'],
                position=player['position'],
                price=player['price'],
                total_points=player['total_points'],
                form=player.get('form'),
                points_per_game=player.get('points_per_game'),
                goals_scored=player.get('goals_scored', 0),
                assists=player.get('assists', 0),
                clean_sheets=player.get('clean_sheets', 0),
                bonus=player.get('bonus', 0),
                selected_by_percent=player.get('selected_by_percent'),
                transfers_in=player.get('transfers_in', 0),
                transfers_out=player.get('transfers_out', 0),
                ep_this=player.get('ep_this'),
                ep_next=player.get('ep_next'),
                status=player.get('status', 'a'),
                news=player.get('news'),
                chance_of_playing_next_round=player.get('chance_of_playing_next_round')
            ))
        
        return AnalysisResponse(players=players, total_count=len(players))
    
    except Exception as e:
        logger.error(f"Error getting transfer targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/differentials", response_model=AnalysisResponse)
async def get_differentials(
    position: Optional[str] = Query(None, description="Filter by position"),
    max_ownership: float = Query(5.0, description="Maximum ownership percentage"),
    min_points: int = Query(50, description="Minimum points required"),
    limit: int = Query(10, description="Number of players to return")
):
    """Get differential players (low ownership, good performance)."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        pos_enum = None
        if position:
            try:
                pos_enum = Position(position.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        players_df = collector.processor.get_differential_players(
            position=pos_enum,
            max_selection=max_ownership,
            min_points=min_points,
            top_n=limit
        )
        
        players = []
        for _, player in players_df.iterrows():
            players.append(PlayerResponse(
                id=player['id'],
                name=player['name'],
                team_name=player['team_name'],
                position=player['position'],
                price=player['price'],
                total_points=player['total_points'],
                form=player.get('form'),
                points_per_game=player.get('points_per_game'),
                goals_scored=player.get('goals_scored', 0),
                assists=player.get('assists', 0),
                clean_sheets=player.get('clean_sheets', 0),
                bonus=player.get('bonus', 0),
                selected_by_percent=player.get('selected_by_percent'),
                transfers_in=player.get('transfers_in', 0),
                transfers_out=player.get('transfers_out', 0),
                ep_this=player.get('ep_this'),
                ep_next=player.get('ep_next'),
                status=player.get('status', 'a'),
                news=player.get('news'),
                chance_of_playing_next_round=player.get('chance_of_playing_next_round')
            ))
        
        return AnalysisResponse(players=players, total_count=len(players))
    
    except Exception as e:
        logger.error(f"Error getting differentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/injuries", response_model=AnalysisResponse)
async def get_injuries(limit: int = Query(10, description="Number of players to return")):
    """Get players with injury concerns."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        players_df = collector.processor.get_injury_concerns()
        
        players = []
        for _, player in players_df.head(limit).iterrows():
            players.append(PlayerResponse(
                id=player['id'],
                name=player['name'],
                team_name=player['team_name'],
                position=player['position'],
                price=player['price'],
                total_points=player['total_points'],
                form=player.get('form'),
                points_per_game=player.get('points_per_game'),
                goals_scored=player.get('goals_scored', 0),
                assists=player.get('assists', 0),
                clean_sheets=player.get('clean_sheets', 0),
                bonus=player.get('bonus', 0),
                selected_by_percent=player.get('selected_by_percent'),
                transfers_in=player.get('transfers_in', 0),
                transfers_out=player.get('transfers_out', 0),
                ep_this=player.get('ep_this'),
                ep_next=player.get('ep_next'),
                status=player.get('status', 'a'),
                news=player.get('news'),
                chance_of_playing_next_round=player.get('chance_of_playing_next_round')
            ))
        
        return AnalysisResponse(players=players, total_count=len(players))
    
    except Exception as e:
        logger.error(f"Error getting injuries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analysis/fixtures", response_model=List[FixtureAnalysisResponse])
async def get_fixture_analysis(
    gameweeks: Optional[str] = Query(None, description="Comma-separated list of gameweeks"),
    limit: int = Query(50, description="Number of fixtures to return")
):
    """Get fixture difficulty analysis."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        gw_list = None
        if gameweeks:
            try:
                gw_list = [int(gw.strip()) for gw in gameweeks.split(",")]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid gameweek format")
        
        fixtures_df = collector.processor.get_fixture_difficulty_analysis(gameweeks=gw_list)
        
        fixtures = []
        for _, fixture in fixtures_df.head(limit).iterrows():
            fixtures.append(FixtureAnalysisResponse(
                gameweek=fixture['gameweek'],
                team_name=fixture['team_name'],
                opponent_name=fixture['opponent_name'],
                difficulty=fixture['difficulty'],
                is_home=fixture['is_home'],
                team_strength=fixture['team_strength'],
                attack_strength=fixture['attack_strength'],
                defence_strength=fixture['defence_strength']
            ))
        
        return fixtures
    
    except Exception as e:
        logger.error(f"Error getting fixture analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary", response_model=SummaryStatsResponse)
async def get_summary_stats():
    """Get summary statistics."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        stats = collector.get_summary_stats()
        return SummaryStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export endpoints
@app.post("/export/csv")
async def export_csv():
    """Export data to CSV files."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        collector.export_data(format="csv")
        return {"status": "success", "message": "Data exported to CSV files in exports/ directory"}
    
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/json")
async def export_json():
    """Export data to JSON files."""
    try:
        collector = get_collector()
        if not collector.processor:
            raise HTTPException(status_code=404, detail="No data available. Collect data first.")
        
        collector.export_data(format="json")
        return {"status": "success", "message": "Data exported to JSON files in exports/ directory"}
    
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download exported files."""
    try:
        file_path = Path("exports") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cache management endpoints
@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached data."""
    try:
        collector = get_collector()
        collector.clear_cache()
        return {"status": "success", "message": "Cache cleared successfully"}
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
