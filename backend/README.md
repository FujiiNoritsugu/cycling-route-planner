# Cycling Route Planner - Backend API

FastAPI backend server for AI-powered cycling route planning with Claude API integration.

## Features

- **POST /api/plan**: Generate cycling route with LLM analysis (SSE streaming)
- **GET /api/weather**: Get weather forecast for specific location and date
- **GET /api/history**: Retrieve past route planning history
- **GET /api/health**: Health check endpoint

## Architecture

- **FastAPI**: Modern async web framework
- **Claude API**: AI-powered route analysis and recommendations
- **SQLite**: Route history storage
- **SSE**: Server-Sent Events for streaming responses

## Setup

### Prerequisites

- Python 3.11+
- uv package manager (or pip)

### Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key

### Running the Server

```bash
# Development mode with auto-reload
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Or from project root
make dev
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest backend/tests/

# With coverage
pytest backend/tests/ --cov=backend --cov-report=term-missing

# Or from project root
make test
```

## Type Checking

```bash
# Run mypy
mypy backend/

# Or from project root
make typecheck
```

## Code Formatting

```bash
# Format with ruff
ruff format backend/

# Lint with ruff
ruff check backend/

# Fix auto-fixable issues
ruff check --fix backend/
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + CORS
│   ├── schemas.py           # Pydantic models (shared with other teams)
│   ├── database.py          # SQLite helpers
│   ├── services/
│   │   ├── claude.py        # Anthropic API client
│   │   └── streaming.py     # SSE utilities
│   └── routers/
│       ├── plan.py          # POST /api/plan
│       ├── weather.py       # GET /api/weather
│       └── history.py       # GET /api/history
├── tests/
│   └── test_api.py          # Integration tests
├── data/                    # SQLite database (auto-created)
├── pyproject.toml
├── requirements.txt
└── README.md
```

## API Documentation

### POST /api/plan

Generate a cycling route plan with AI analysis.

**Request:**
```json
{
  "origin": {"lat": 34.573, "lng": 135.483, "name": "堺市上野芝"},
  "destination": {"lat": 34.396, "lng": 135.757, "name": "吉野山"},
  "preferences": {
    "difficulty": "moderate",
    "avoid_traffic": true,
    "prefer_scenic": true,
    "max_distance_km": 100,
    "max_elevation_gain_m": 1500
  },
  "departure_time": "2025-03-15T07:00:00"
}
```

**Response:** Server-Sent Events stream

```
event: route_data
data: {"segments": [...], "total_distance_km": 85.3, ...}

event: weather
data: [{"time": "2025-03-15T07:00:00", "temperature": 18.0, ...}]

event: token
data: ルート

event: token
data: 分析

event: done
data: {"status": "complete", "plan_id": "..."}
```

### GET /api/weather

Get weather forecast for a location.

**Parameters:**
- `lat`: Latitude (-90 to 90)
- `lng`: Longitude (-180 to 180)
- `date`: Date in ISO format (YYYY-MM-DD)

**Response:**
```json
{
  "data": {
    "time": "2025-03-15T00:00:00",
    "temperature": 20.0,
    "wind_speed": 4.0,
    "wind_direction": 135.0,
    "precipitation_probability": 15.0,
    "weather_code": 1,
    "description": "晴れ時々曇り"
  }
}
```

### GET /api/history

Retrieve route planning history.

**Parameters:**
- `limit`: Max number of plans to return (1-100, default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "...",
      "segments": [...],
      "total_distance_km": 85.3,
      "llm_analysis": "...",
      "created_at": "2025-03-15T10:30:00"
    }
  ]
}
```

## Dependencies on Other Modules

This backend expects the `planner` module (to be implemented by route-planner agent):

```python
from planner import route_generator, weather_client, elevation_service
```

Current implementation uses mock data for these dependencies.

## Notes

- **schemas.py** is the source of truth for data models. Other teams should import these models.
- External API calls to planner module are currently mocked and will be replaced when available.
- Claude API requires `ANTHROPIC_API_KEY` environment variable.
- SQLite database is created automatically in `backend/data/`.

## License

MIT
