#!/usr/bin/env python3
"""
Basic tests for the FPL Data Collector.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch

from src.models import Position, Player, Team, Fixture, Gameweek
from src.exceptions import APIError, ValidationError, DataProcessingError


def test_position_enum():
    """Test Position enum values."""
    assert Position.GK.value == "GK"
    assert Position.DEF.value == "DEF"
    assert Position.MID.value == "MID"
    assert Position.FWD.value == "FWD"


def test_player_model():
    """Test Player model creation and validation."""
    player_data = {
        "id": 1,
        "first_name": "Test",
        "second_name": "Player",
        "web_name": "T. Player",
        "element_type": 3,  # MID
        "team": 1,
        "now_cost": 85,  # 8.5 million
    }
    
    player = Player(**player_data)
    
    assert player.id == 1
    assert player.full_name == "Test Player"
    assert player.position == Position.MID
    assert player.price == 8.5
    assert player.status == "a"  # Default value


def test_player_model_validation():
    """Test Player model validation."""
    # Test invalid element_type
    with pytest.raises(ValueError):
        Player(
            id=1,
            first_name="Test",
            second_name="Player",
            web_name="T. Player",
            element_type=5,  # Invalid
            team=1,
            now_cost=85,
        )


def test_team_model():
    """Test Team model creation."""
    team_data = {
        "id": 1,
        "name": "Test Team",
        "short_name": "TST",
        "code": 1,
        "strength": 1000,
        "strength_overall_home": 1000,
        "strength_overall_away": 1000,
        "strength_attack_home": 1000,
        "strength_attack_away": 1000,
        "strength_defence_home": 1000,
        "strength_defence_away": 1000,
        "pulse_id": 1,
    }
    
    team = Team(**team_data)
    
    assert team.id == 1
    assert team.name == "Test Team"
    assert team.short_name == "TST"


def test_fixture_model():
    """Test Fixture model creation."""
    fixture_data = {
        "id": 1,
        "code": 1,
        "team_h": 1,
        "team_a": 2,
        "event": 1,
        "event_name": "Gameweek 1",
        "is_home": True,
        "difficulty": 2,
    }
    
    fixture = Fixture(**fixture_data)
    
    assert fixture.id == 1
    assert fixture.team_h == 1
    assert fixture.team_a == 2
    assert fixture.event == 1
    assert fixture.difficulty == 2


def test_gameweek_model():
    """Test Gameweek model creation."""
    gameweek_data = {
        "id": 1,
        "name": "Gameweek 1",
        "deadline_time": "2024-08-16T11:00:00Z",
        "is_current": True,
        "is_next": False,
    }
    
    gameweek = Gameweek(**gameweek_data)
    
    assert gameweek.id == 1
    assert gameweek.name == "Gameweek 1"
    assert gameweek.is_current is True
    assert gameweek.is_next is False


@pytest.mark.asyncio
async def test_api_client_initialization():
    """Test API client initialization."""
    from src.api_client import FPLAPIClient
    
    async with FPLAPIClient() as client:
        assert client is not None
        assert hasattr(client, 'config')
        assert hasattr(client, 'session')


def test_sync_api_client_initialization():
    """Test synchronous API client initialization."""
    from src.api_client import FPLAPIClientSync
    
    client = FPLAPIClientSync()
    assert client is not None
    assert hasattr(client, 'config')
    assert hasattr(client, 'session')


def test_config_loading():
    """Test configuration loading."""
    from src.config import config
    
    assert config is not None
    assert hasattr(config, 'api')
    assert hasattr(config, 'data')
    assert hasattr(config, 'logging')
    
    # Test API config
    assert config.api.BOOTSTRAP_STATIC_URL is not None
    assert config.api.TIMEOUT > 0
    assert config.api.MAX_RETRIES > 0
    
    # Test data config
    assert config.data.DATA_DIR is not None
    assert config.data.CACHE_DIR is not None
    assert config.data.EXPORT_DIR is not None


def test_exceptions():
    """Test custom exceptions."""
    # Test base exception
    base_exc = Exception("Test")
    assert str(base_exc) == "Test"
    
    # Test API error
    api_error = APIError("API test error")
    assert str(api_error) == "API test error"
    
    # Test validation error
    val_error = ValidationError("Validation test error")
    assert str(val_error) == "Validation test error"
    
    # Test data processing error
    proc_error = DataProcessingError("Processing test error")
    assert str(proc_error) == "Processing test error"


@pytest.mark.asyncio
async def test_collector_initialization():
    """Test collector initialization."""
    from src.collector import FPLDataCollector
    
    collector = FPLDataCollector(use_async=True, cache_data=True)
    
    assert collector is not None
    assert collector.use_async is True
    assert collector.cache_data is True
    assert collector.fpl_data is None
    assert collector.processor is None


def test_data_processor_initialization():
    """Test data processor initialization with mock data."""
    from src.data_processor import FPLDataProcessor
    from src.models import FPLData, Player, Team
    
    # Create mock data
    mock_player = Player(
        id=1,
        first_name="Test",
        second_name="Player",
        web_name="T. Player",
        element_type=3,
        team=1,
        now_cost=85,
    )
    
    mock_team = Team(
        id=1,
        name="Test Team",
        short_name="TST",
        code=1,
        strength=1000,
        strength_overall_home=1000,
        strength_overall_away=1000,
        strength_attack_home=1000,
        strength_attack_away=1000,
        strength_defence_home=1000,
        strength_defence_away=1000,
        pulse_id=1,
    )
    
    mock_fpl_data = FPLData(
        players=[mock_player],
        teams=[mock_team],
        fixtures=[],
        gameweeks=[],
        events=[],
    )
    
    processor = FPLDataProcessor(mock_fpl_data)
    
    assert processor is not None
    assert processor.data is mock_fpl_data
    assert hasattr(processor, 'players_df')
    assert hasattr(processor, 'teams_df')
    assert hasattr(processor, 'fixtures_df')


if __name__ == "__main__":
    # Run basic tests
    print("Running basic tests...")
    
    test_position_enum()
    test_player_model()
    test_team_model()
    test_fixture_model()
    test_gameweek_model()
    test_config_loading()
    test_exceptions()
    
    print("All basic tests passed!")
