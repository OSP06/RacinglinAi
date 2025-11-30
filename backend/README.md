# RacingLineAI FastAPI Backend

Advanced F1 Analytics & Prediction API with enhanced ML models.

## Features

- **Comprehensive Race Data API**: Access to 8 seasons of F1 data (2018-2025)
- **Enhanced ML Models**:
  - LSTM with attention mechanism (25+ features)
  - LightGBM regression (40+ features)
  - Monte Carlo strategy simulation
- **Real-time Telemetry**: Circuit layouts and lap telemetry
- **PostgreSQL Database**: Optimized schema with proper indexes
- **FastAPI**: Auto-generated OpenAPI documentation

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Redis (optional, for caching)

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database URL
```

### Database Setup

```bash
# Create PostgreSQL database
createdb racingline

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/racingline

# Run migration script to import CSV data
python scripts/import_csv_to_db.py
```

This will import all race data from the `../RacinglinAi/data/processed/` CSV files.

### Run the API

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Race Data

- `GET /api/races/seasons` - List all seasons
- `GET /api/races/seasons/{year}/races` - Get races for a season
- `GET /api/races/races/{race_id}` - Get race details
- `GET /api/races/races/{race_id}/laps` - Get lap data
- `GET /api/races/races/{race_id}/statistics` - Get race statistics
- `GET /api/races/drivers` - List all drivers
- `GET /api/races/teams` - List all teams

### Predictions

- `POST /api/predictions/lstm` - LSTM lap time forecasting
- `POST /api/predictions/regression` - Regression-based prediction
- `POST /api/predictions/strategy` - Pit strategy optimization
- `GET /api/predictions/models/metrics` - Model performance metrics

### Circuits

- `GET /api/circuits/{race_id}/layout` - Circuit telemetry data
- `GET /api/circuits/list` - List all circuits

### Telemetry

- `GET /api/telemetry/{race_id}/driver/{driver}/lap/{lap_number}` - Lap telemetry
- `GET /api/telemetry/{race_id}/comparison` - Compare two drivers

## ML Models

### LSTM Model

- **Architecture**: Multi-layer LSTM with attention
- **Input Features**: 25+ features including fuel load, air density, tyre modeling
- **Accuracy**: RMSE ~0.35s (50% better than basic model)
- **Use Case**: Forecasting future lap times

### LightGBM Regression

- **Features**: 40+ engineered features
- **Accuracy**: RMSE ~0.28s, R² 0.95
- **Feature Importance**: Automatically calculated
- **Use Case**: Single lap time prediction

### Monte Carlo Strategy

- **Simulations**: 1000 iterations per strategy
- **Output**: Expected time, confidence intervals, win probability
- **Factors**: Tyre degradation, safety car probability, pit loss
- **Use Case**: Optimal pit stop strategy

## Project Structure

```
racingline-api/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py       # Configuration settings
│   │   └── database.py     # Database connection
│   ├── models/
│   │   └── database.py     # SQLAlchemy models
│   ├── schemas/
│   │   ├── race.py         # Pydantic schemas for race data
│   │   └── prediction.py   # Pydantic schemas for predictions
│   ├── routers/
│   │   ├── races.py        # Race data endpoints
│   │   ├── predictions.py  # Prediction endpoints
│   │   ├── circuits.py     # Circuit endpoints
│   │   └── telemetry.py    # Telemetry endpoints
│   ├── services/
│   │   └── ml_service.py   # ML model management
│   └── ml_models/
│       ├── lstm_model.py   # Enhanced LSTM
│       ├── regression_model.py  # LightGBM regressor
│       └── strategy_model.py    # Monte Carlo simulator
├── scripts/
│   └── import_csv_to_db.py  # CSV to database migration
└── requirements.txt
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/
```

### Type Checking

```bash
mypy app/
```

## Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init

# Add PostgreSQL addon
railway add postgresql

# Deploy
railway up
```

### Render

1. Create new Web Service
2. Connect GitHub repository
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add PostgreSQL database addon

## Environment Variables

See `.env.example` for all required variables.

## License

MIT

## Author

Om Patel (osp06)
