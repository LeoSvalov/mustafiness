# Fantasy Premier League Squad Builder

A comprehensive, data-driven squad builder for Fantasy Premier League that uses advanced data science and machine learning approaches to optimize team selection.

## 🚀 Features

### Core Functionality
- **Multi-Strategy Optimization**: Build squads using different strategies (value, form, fixtures, differentials, balanced)
- **Machine Learning Integration**: Advanced ML models for player performance prediction
- **Fixture Analysis**: Comprehensive fixture difficulty assessment
- **Risk Management**: Player risk assessment and mitigation
- **Budget Optimization**: Efficient budget allocation within FPL constraints
- **Team Diversity**: Ensures optimal team and position distribution

### Advanced Features
- **Player Clustering**: Groups similar players for better selection
- **Market Efficiency Analysis**: Identifies undervalued players
- **Transfer Recommendations**: Smart transfer suggestions
- **Captain Selection**: Data-driven captain recommendations
- **Squad Comparison**: Compare different squad configurations
- **Custom Constraints**: Flexible constraint system for personalized squads

## 🏗️ Architecture

### Core Components

1. **SquadBuilder** (`src/squad_builder.py`)
   - Base squad building logic
   - Multiple optimization strategies
   - Constraint handling
   - Player scoring algorithms

2. **MLSquadBuilder** (`src/ml_squad_builder.py`)
   - Machine learning-enhanced squad building
   - Player performance prediction
   - Clustering analysis
   - Ensemble methods

3. **SquadBuilderService** (`src/squad_builder_service.py`)
   - API service layer
   - Request/response handling
   - Integration with existing API structure

### Data Science Approaches

#### Player Scoring Model
Each player is scored using multiple factors:
- **Form Score**: Recent performance (25% weight)
- **Fixture Difficulty**: Upcoming fixture analysis (20% weight)
- **Team Strength**: Team performance metrics (15% weight)
- **Differential Score**: Ownership-based differential potential (15% weight)
- **Expected Points**: FPL's expected points (20% weight)
- **Risk Factor**: Injury, availability, and market risks (5% weight)

#### Machine Learning Models
- **Random Forest**: Player points prediction
- **Gradient Boosting**: Form and risk prediction
- **K-Means Clustering**: Player similarity grouping
- **Ensemble Methods**: Multiple model combination for better predictions

#### Optimization Strategies
1. **Value-Based**: Points per million optimization
2. **Form-Based**: Current form prioritization
3. **Fixture-Based**: Upcoming fixture difficulty focus
4. **Differential-Based**: Low ownership, high potential players
5. **Balanced**: Ensemble of all strategies

## 📊 Data Sources

The squad builder utilizes all available FPL data:
- Player statistics (goals, assists, clean sheets, etc.)
- Team performance metrics
- Fixture difficulty ratings
- Player form and ICT indices
- Transfer activity and ownership percentages
- Expected points (FPL's predictions)
- Injury and availability data

## 🛠️ Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have the required ML libraries:
```bash
pip install scikit-learn>=1.3.0
```

## 🎯 Usage

### Basic Squad Building

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

### ML-Optimized Squad Building

```python
# Use ML-enhanced squad building
ml_result = squad_service.build_squad(constraints, use_ml=True)

# Access ML-specific analysis
ml_analysis = ml_result.analysis.get('ml_analysis', {})
print(f"ML Predicted points: {ml_analysis.get('total_predicted_points', 0):.1f}")
print(f"Market efficiency: {ml_analysis.get('avg_market_efficiency', 0):.2f}")
```

### Custom Constraints

```python
custom_constraints = SquadConstraintsRequest(
    budget=95.0,
    max_players_per_team=2,
    formation="3-5-2",
    must_have_players=[123, 456],  # Player IDs
    must_not_have_players=[789],
    min_players_per_position={
        "GK": 2,
        "DEF": 3,
        "MID": 5,
        "FWD": 3
    }
)
```

### Captain Recommendations

```python
squad_player_ids = [player['player_id'] for player in result.squad]
captain_recs = squad_service.get_captain_recommendations(squad_player_ids, 5)

for rec in captain_recs:
    print(f"{rec['name']} - Form: {rec['form_score']:.2f}")
```

### Transfer Recommendations

```python
current_squad = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
transfer_recs = squad_service.get_transfer_recommendations(
    current_squad, constraints, num_recommendations=5, use_ml=True
)

for rec in transfer_recs:
    print(f"{rec.transfer_out['name']} → {rec.transfer_in['name']}")
    print(f"Upgrade value: {rec.upgrade_value:.3f}")
```

### Player Analysis

```python
player_analysis = squad_service.get_player_analysis(player_id=123)
print(f"Analysis for {player_analysis['name']}:")
print(f"Total score: {player_analysis['total_score']:.3f}")
print(f"Risk factor: {player_analysis['risk_factor']:.3f}")
print(f"Upcoming fixtures: {len(player_analysis['upcoming_fixtures'])}")
```

### Squad Comparison

```python
squad1_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
squad2_ids = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

comparison = squad_service.get_squad_comparison(squad1_ids, squad2_ids)
print(f"Cost difference: £{comparison['differences']['cost_difference']:.1f}m")
print(f"Points difference: {comparison['differences']['points_difference']:.1f}")
```

## 🧪 Running Examples

Run the comprehensive example script:

```bash
python examples/squad_builder_example.py
```

This will demonstrate:
- Basic squad building
- ML-optimized squad building
- Captain recommendations
- Transfer recommendations
- Player analysis
- Squad comparison
- Custom constraints

## 📈 Performance Metrics

The squad builder evaluates squads using multiple metrics:

### Standard Metrics
- **Total Cost**: Squad budget utilization
- **Expected Points**: FPL's expected points total
- **Form Analysis**: Average player form
- **Risk Analysis**: Squad risk assessment
- **Position Balance**: Formation compliance
- **Team Diversity**: Number of teams represented

### ML-Enhanced Metrics
- **Predicted Points**: ML model predictions
- **Market Efficiency**: Value for money analysis
- **Cluster Diversity**: Player similarity distribution
- **Confidence Intervals**: Prediction uncertainty
- **Similarity Scores**: Player performance comparison

## 🔧 Configuration

### Squad Constraints

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `budget` | float | 100.0 | Total squad budget (£m) |
| `max_players_per_team` | int | 3 | Maximum players per team |
| `formation` | str | None | Preferred formation |
| `captain_id` | int | None | Designated captain |
| `vice_captain_id` | int | None | Designated vice-captain |
| `must_have_players` | List[int] | [] | Players that must be included |
| `must_not_have_players` | List[int] | [] | Players to exclude |
| `min_players_per_position` | Dict | Default FPL rules | Minimum players per position |
| `max_players_per_position` | Dict | Default FPL rules | Maximum players per position |

### ML Model Parameters

The ML models can be tuned by modifying the parameters in `MLSquadBuilder._initialize_ml_models()`:

```python
# Example: Adjust Random Forest parameters
RandomForestRegressor(
    n_estimators=200,  # More trees
    max_depth=10,      # Control tree depth
    random_state=42
)
```

## 🚨 Error Handling

The squad builder includes comprehensive error handling:

- **Data Validation**: Ensures data integrity
- **Constraint Validation**: Validates squad constraints
- **ML Model Fallbacks**: Graceful degradation if ML models fail
- **API Error Handling**: Proper HTTP error responses

## 🔮 Future Enhancements

### Phase 2: External Data Integration
- **Reddit Sentiment Analysis**: Community sentiment integration
- **Twitter/X Analysis**: Social media sentiment
- **News Analysis**: Injury and transfer news impact
- **Weather Data**: Weather impact on performance

### Advanced ML Features
- **Deep Learning Models**: Neural networks for prediction
- **Time Series Analysis**: Historical performance trends
- **Ensemble Learning**: Advanced model combination
- **Feature Engineering**: Automated feature creation

### Real-time Features
- **Live Data Integration**: Real-time performance updates
- **Dynamic Pricing**: Price change impact analysis
- **Injury Monitoring**: Real-time availability tracking
- **Form Tracking**: Live form calculation

## 📝 API Endpoints

The squad builder integrates with the existing API structure:

- `POST /squad/build` - Build optimal squad
- `GET /squad/captain-recommendations` - Get captain suggestions
- `POST /squad/transfer-recommendations` - Get transfer advice
- `GET /squad/player-analysis/{player_id}` - Detailed player analysis
- `POST /squad/compare` - Compare two squads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Fantasy Premier League for providing the data
- The FPL community for insights and feedback
- Open source ML libraries (scikit-learn, pandas, numpy)

---

**Note**: This squad builder is for educational and entertainment purposes. Always make your own decisions when playing Fantasy Premier League!
