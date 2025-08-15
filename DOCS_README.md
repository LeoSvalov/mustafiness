# Mustafiness - Fantasy Premier League Assistant

## Features

- **Complete Data Collection**: Fetches all available FPL data including players, teams, fixtures, and gameweeks
- **Squad Builder**: AI-powered squad optimization using data science and machine learning approaches
- **Async Support**: High-performance async API client with rate limiting and retry logic
- **Data Validation**: Comprehensive data models using Pydantic for type safety and validation
- **Caching**: Intelligent caching system to reduce API calls and improve performance
- **Data Analysis**: Built-in analysis tools for player performance, team statistics, and fixture difficulty
- **Multiple Export Formats**: Export data to CSV, JSON, and other formats
- **Error Handling**: Robust error handling with custom exceptions
- **Configuration Management**: Flexible configuration system with environment variable support
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mustafiness
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install as a package:
```bash
pip install -e .
```

## Quick Start

### Option 1: API Service (Recommended)

Run the API service for easy integration:

```bash
# Start the API server
python run_api_server.py

# Or with custom settings
python run_api_server.py --host 0.0.0.0 --port 8000 --reload
```

Then visit:
- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Option 2: Direct Python Usage

```python
import asyncio
from src.collector import collect_fpl_data

async def main():
    # Collect all FPL data
    collector = await collect_fpl_data(force_refresh=False, export_format="csv")
    
    # Get summary statistics
    stats = collector.get_summary_stats()
    print(f"Total players: {stats['total_players']}")
    print(f"Current gameweek: {stats['current_gameweek']}")

# Run the async function
asyncio.run(main())
```

### Advanced Usage

#### Using the API Service

```python
import requests

# Initialize API client
base_url = "http://localhost:8000"

# Collect data
response = requests.post(f"{base_url}/collect")
print(f"Data collection: {response.json()}")

# Get top performers
response = requests.get(f"{base_url}/analysis/top-performers?limit=10")
top_players = response.json()
print(f"Top 10 players: {top_players}")

# Get value players
response = requests.get(f"{base_url}/analysis/value-players?min_points=50&limit=10")
value_players = response.json()
print(f"Value players: {value_players}")

# Export data
response = requests.post(f"{base_url}/export/csv")
print(f"Export result: {response.json()}")
```

#### Using Direct Python

```python
import asyncio
from src.collector import FPLDataCollector
from src.models import Position

async def main():
    # Initialize collector
    collector = FPLDataCollector(use_async=True, cache_data=True)
    
    # Collect data
    fpl_data = await collector.collect_all_data(force_refresh=False)
    
    # Get players by position
    goalkeepers = collector.get_players(position="GK")
    defenders = collector.get_players(position="DEF")
    
    # Use data processor for analysis
    processor = collector.processor
    
    # Get top performers
    top_players = processor.get_top_performers(top_n=10)
    print("Top 10 players:", top_players)
    
    # Get value players
    value_players = processor.get_value_players(min_points=50, top_n=10)
    print("Best value players:", value_players)
    
    # Get fixture analysis
    fixture_analysis = processor.get_fixture_difficulty_analysis()
    print("Fixture difficulty:", fixture_analysis)
    
    # Export data
    collector.export_data(format="csv")

asyncio.run(main())
```

## API Service

Mustafiness includes a complete RESTful API service built with FastAPI. This allows you to run it as an independent component with all necessary endpoints.

### Running the API Service

```bash
# Basic run
python run_api_server.py

# With custom settings
python run_api_server.py --host 0.0.0.0 --port 8000 --reload --log-level DEBUG

# Using Docker
docker build -t fpl-api .
docker run -p 8000:8000 fpl-api

# Using Docker Compose
docker-compose up -d
```

### API Endpoints

#### Health & Status
- `GET /` - Root endpoint with health status
- `GET /health` - Health check
- `GET /status` - API status and data availability

#### Data Collection
- `POST /collect` - Collect all FPL data
- `POST /collect/background` - Start background data collection

#### Data Retrieval
- `GET /players` - Get players with optional filtering
- `GET /teams` - Get all teams
- `GET /fixtures` - Get fixtures with optional gameweek filtering
- `GET /gameweeks` - Get all gameweeks
- `GET /current-gameweek` - Get current gameweek

#### Analysis
- `GET /analysis/top-performers` - Get top performing players
- `GET /analysis/value-players` - Get value players (points per million)
- `GET /analysis/form-players` - Get players with good form
- `GET /analysis/transfer-targets` - Get transfer targets
- `GET /analysis/differentials` - Get differential players
- `GET /analysis/injuries` - Get injury concerns
- `GET /analysis/fixtures` - Get fixture difficulty analysis
- `GET /summary` - Get summary statistics

#### Squad Builder
- `POST /squad/build` - Build optimal squad using data science and ML
- `GET /squad/captain-recommendations` - Get captain suggestions
- `POST /squad/transfer-recommendations` - Get transfer advice
- `GET /squad/player-analysis/{player_id}` - Detailed player analysis
- `POST /squad/compare` - Compare two squads

#### Export
- `POST /export/csv` - Export data to CSV files
- `POST /export/json` - Export data to JSON files
- `GET /download/{filename}` - Download exported files

#### Cache Management
- `POST /cache/clear` - Clear all cached data

### API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Example API Usage

```python
import requests

# Initialize client
base_url = "http://localhost:8000"

# Check health
response = requests.get(f"{base_url}/health")
print(f"API Health: {response.json()}")

# Collect data
response = requests.post(f"{base_url}/collect")
print(f"Data Collection: {response.json()}")

# Get top performers
response = requests.get(f"{base_url}/analysis/top-performers?limit=5")
top_players = response.json()
for player in top_players['players']:
    print(f"{player['name']} - {player['total_points']} points")

# Get value players
response = requests.get(f"{base_url}/analysis/value-players?min_points=50&limit=5")
value_players = response.json()
for player in value_players['players']:
    print(f"{player['name']} - {player['price']}M")

# Export data
response = requests.post(f"{base_url}/export/csv")
print(f"Export: {response.json()}")
```

### Docker Deployment

```bash
# Build and run with Docker
docker build -t fpl-api .
docker run -p 8000:8000 -v $(pwd)/exports:/app/exports fpl-api

# Or use Docker Compose
docker-compose up -d
```

## Data Models

The library provides comprehensive data models for all FPL entities:

### Player
- Basic information (name, team, position)
- Price and transfer data
- Performance statistics (points, goals, assists, etc.)
- Form and ICT indices
- Availability and injury status
- Expected points

### Team
- Team information and statistics
- Strength ratings (overall, attack, defence)
- League position and form
- Goals for/against

### Fixture
- Match details and scheduling
- Team matchups and difficulty ratings
- Scores and status

### Gameweek
- Gameweek information and deadlines
- Current/next gameweek status

## Data Analysis Features

### Player Analysis
- **Top Performers**: Players with highest points, form, or other metrics
- **Value Players**: Players with best points per million
- **Form Players**: Players with good recent form
- **Transfer Targets**: Players with high transfer activity
- **Differential Players**: Low ownership players with good performance
- **Injury Concerns**: Players with availability issues

### Team Analysis
- **Team Statistics**: Comprehensive team performance metrics
- **Fixture Difficulty**: Analysis of upcoming fixture difficulty
- **Position Distribution**: Player distribution by position

### Fixture Analysis
- **Difficulty Ratings**: Fixture difficulty for upcoming gameweeks
- **Team Strength**: Home/away strength analysis

## Squad Builder

The squad builder is a powerful AI-driven tool that uses data science and machine learning to optimize Fantasy Premier League squad selection.

### Features

- **Multi-Strategy Optimization**: Build squads using different strategies (value, form, fixtures, differentials, balanced)
- **Machine Learning Integration**: Advanced ML models for player performance prediction
- **Fixture Analysis**: Comprehensive fixture difficulty assessment
- **Risk Management**: Player risk assessment and mitigation
- **Budget Optimization**: Efficient budget allocation within FPL constraints
- **Team Diversity**: Ensures optimal team and position distribution

### Usage

#### Basic Squad Building

```python
from src.api_client import FPLAPIClient
from src.squad_builder_service import SquadBuilderService, SquadConstraintsRequest

# Initialize
client = FPLAPIClient()
fpl_data = client.get_all_data()
squad_service = SquadBuilderService(fpl_data)

# Build squad
constraints = SquadConstraintsRequest(
    budget=100.0,
    max_players_per_team=3,
    formation="4-4-2"
)

result = squad_service.build_squad(constraints, use_ml=False)
print(f"Squad cost: £{result.analysis['total_cost']:.1f}m")
print(f"Expected points: {result.analysis['total_expected_points']:.1f}")
```

#### ML-Optimized Squad Building

```python
# Use ML-enhanced squad building
ml_result = squad_service.build_squad(constraints, use_ml=True)

# Access ML-specific analysis
ml_analysis = ml_result.analysis.get('ml_analysis', {})
print(f"ML Predicted points: {ml_analysis.get('total_predicted_points', 0):.1f}")
print(f"Market efficiency: {ml_analysis.get('avg_market_efficiency', 0):.2f}")
```

#### Captain and Transfer Recommendations

```python
# Get captain recommendations
squad_player_ids = [player['player_id'] for player in result.squad]
captain_recs = squad_service.get_captain_recommendations(squad_player_ids, 5)

# Get transfer recommendations
transfer_recs = squad_service.get_transfer_recommendations(
    current_squad, constraints, num_recommendations=5, use_ml=True
)
```

### Running Examples

```bash
# Run the comprehensive squad builder example
python examples/squad_builder_example.py
```

For detailed documentation, see [SQUAD_BUILDER_README.md](SQUAD_BUILDER_README.md).
- **Player Performance**: Expected performance based on fixtures

## Configuration

The library uses a flexible configuration system:

### Environment Variables
```bash
# API settings
export FPL_API_TIMEOUT=30
export FPL_MAX_RETRIES=3

# Data settings
export FPL_DATA_DIR="./data"
export FPL_DATABASE_URL="sqlite:///fpl_data.db"

# Logging settings
export FPL_LOG_LEVEL="INFO"
export FPL_LOG_FILE="./fpl.log"
```

### Configuration File
You can also modify the configuration in `src/config.py`:

```python
from src.config import config

# Modify API settings
config.api.TIMEOUT = 30
config.api.MAX_RETRIES = 3

# Modify data directories
config.data.DATA_DIR = Path("./custom_data")
```

## Caching

The library includes an intelligent caching system:

- **Bootstrap Data**: Cached for 1 hour by default
- **Player Details**: Cached for 6 hours by default
- **Automatic Refresh**: Stale cache is automatically refreshed
- **Force Refresh**: Option to bypass cache when needed

```python
# Force refresh all data
collector = await collect_fpl_data(force_refresh=True)

# Clear cache manually
collector.clear_cache()
```

## Error Handling

The library provides comprehensive error handling:

```python
from src.exceptions import APIError, ValidationError, DataProcessingError

try:
    collector = await collect_fpl_data()
except APIError as e:
    print(f"API error: {e}")
except ValidationError as e:
    print(f"Data validation error: {e}")
except DataProcessingError as e:
    print(f"Data processing error: {e}")
```

## Export Options

### CSV Export
```python
collector.export_data(format="csv")
# Exports to exports/ directory:
# - players.csv
# - teams.csv
# - fixtures.csv
# - team_analysis.csv
# - fixture_analysis.csv
# - players_gk.csv, players_def.csv, etc.
# - top_performers.csv
# - value_players.csv
# - form_players.csv
# - transfer_targets.csv
# - differential_players.csv
# - injury_concerns.csv
# - expected_points.csv
```

### JSON Export
```python
collector.export_data(format="json")
# Exports to exports/ directory:
# - players.json
# - teams.json
# - fixtures.json
# - gameweeks.json
# - summary_stats.json
```

## API Reference

### FPLDataCollector

Main class for data collection and management.

#### Methods
- `collect_all_data(force_refresh=False)`: Collect all FPL data
- `get_players(position=None, team_id=None)`: Get players with filtering
- `get_teams()`: Get all teams
- `get_fixtures(gameweek=None)`: Get fixtures with optional gameweek filtering
- `get_gameweeks()`: Get all gameweeks
- `get_current_gameweek()`: Get current gameweek
- `get_next_gameweek()`: Get next gameweek
- `export_data(format="csv", output_dir=None)`: Export data
- `get_summary_stats()`: Get summary statistics
- `clear_cache()`: Clear cached data

### FPLDataProcessor

Data analysis and processing utilities.

#### Methods
- `get_top_performers(position=None, metric="total_points", top_n=10)`: Get top performers
- `get_value_players(position=None, min_points=50, top_n=10)`: Get value players
- `get_form_players(position=None, min_form=5.0, top_n=10)`: Get form players
- `get_transfer_targets(position=None, min_transfers_in=1000)`: Get transfer targets
- `get_differential_players(position=None, max_selection=5.0, min_points=50)`: Get differentials
- `get_injury_concerns()`: Get injury concerns
- `get_expected_points_analysis()`: Get expected points analysis
- `get_fixture_difficulty_analysis(gameweeks=None)`: Get fixture analysis
- `get_team_analysis()`: Get team analysis
- `get_position_analysis()`: Get position analysis

## Examples

### Squad Building Analysis
```python
async def analyze_squad_options():
    collector = await collect_fpl_data()
    processor = collector.processor
    
    # Get budget options for each position
    budget_gk = processor.get_value_players(position=Position.GK, min_points=30, top_n=5)
    budget_def = processor.get_value_players(position=Position.DEF, min_points=40, top_n=10)
    budget_mid = processor.get_value_players(position=Position.MID, min_points=50, top_n=15)
    budget_fwd = processor.get_value_players(position=Position.FWD, min_points=40, top_n=8)
    
    # Get premium options
    premium_players = processor.get_top_performers(top_n=20)
    
    # Get differentials
    differentials = processor.get_differential_players(max_selection=5.0, min_points=60)
    
    return {
        'budget_gk': budget_gk,
        'budget_def': budget_def,
        'budget_mid': budget_mid,
        'budget_fwd': budget_fwd,
        'premium_players': premium_players,
        'differentials': differentials
    }
```

### Fixture Analysis
```python
async def analyze_fixtures():
    collector = await collect_fpl_data()
    processor = collector.processor
    
    # Get fixture difficulty for next 5 gameweeks
    fixture_analysis = processor.get_fixture_difficulty_analysis()
    
    # Find teams with easy fixtures
    easy_fixtures = fixture_analysis[fixture_analysis['difficulty'] <= 2]
    
    # Get players from teams with easy fixtures
    easy_team_ids = easy_fixtures['team_id'].unique()
    easy_team_players = []
    
    for team_id in easy_team_ids:
        team_players = processor.get_players_by_team(team_id)
        easy_team_players.append(team_players)
    
    return {
        'fixture_analysis': fixture_analysis,
        'easy_fixtures': easy_fixtures,
        'easy_team_players': easy_team_players
    }
```

### Transfer Analysis
```python
async def analyze_transfers():
    collector = await collect_fpl_data()
    processor = collector.processor
    
    # Get popular transfer targets
    transfer_targets = processor.get_transfer_targets(min_transfers_in=10000)
    
    # Get players being transferred out
    transfer_outs = processor.get_transfer_targets(min_transfers_in=5000)
    transfer_outs = transfer_outs[transfer_outs['transfer_balance'] < 0]
    
    # Get differentials to consider
    differentials = processor.get_differential_players(max_selection=3.0, min_points=70)
    
    return {
        'transfer_targets': transfer_targets,
        'transfer_outs': transfer_outs,
        'differentials': differentials
    }
```

## Performance Considerations

- **Async Operations**: Use async/await for better performance with multiple API calls
- **Caching**: Enable caching to reduce API calls and improve response times
- **Batch Processing**: Player details are collected in batches to avoid overwhelming the API
- **Rate Limiting**: Built-in rate limiting to respect API limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Fantasy Premier League for providing the API
- The FPL community for inspiration and feedback
