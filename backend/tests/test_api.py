"""Integration tests for FastAPI endpoints.

Tests use httpx.AsyncClient to test the API endpoints.
External API calls are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.claude import ClaudeService


@pytest.fixture
def mock_claude_service() -> ClaudeService:
    """Create mocked ClaudeService.

    Returns:
        Mocked ClaudeService instance.
    """
    # Mock the service without requiring API key
    with patch.object(ClaudeService, "__init__", lambda self, api_key=None: None):
        service = ClaudeService()
        service.api_key = "mock-api-key"
        service.client = MagicMock()
        return service


@pytest.fixture
async def client(mock_claude_service: ClaudeService) -> AsyncClient:
    """Create async HTTP client for testing.

    Args:
        mock_claude_service: Mocked Claude service.

    Yields:
        Configured AsyncClient.
    """
    # Override dependency
    from backend.app.services.claude import get_claude_service

    async def override_claude_service() -> ClaudeService:
        return mock_claude_service

    app.dependency_overrides[get_claude_service] = override_claude_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test root endpoint returns welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Cycling Route Planner" in data["message"]


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_weather(client: AsyncClient) -> None:
    """Test weather endpoint with valid parameters."""
    response = await client.get(
        "/api/weather",
        params={
            "lat": 34.573,
            "lng": 135.483,
            "date": "2025-03-15",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "temperature" in data["data"]
    assert "wind_speed" in data["data"]


@pytest.mark.asyncio
async def test_get_weather_invalid_date(client: AsyncClient) -> None:
    """Test weather endpoint with invalid date format."""
    response = await client.get(
        "/api/weather",
        params={
            "lat": 34.573,
            "lng": 135.483,
            "date": "invalid-date",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_weather_invalid_coords(client: AsyncClient) -> None:
    """Test weather endpoint with invalid coordinates."""
    response = await client.get(
        "/api/weather",
        params={
            "lat": 999,  # Invalid latitude
            "lng": 135.483,
            "date": "2025-03-15",
        },
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_history_empty(client: AsyncClient) -> None:
    """Test history endpoint with no plans."""
    response = await client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_history_with_limit(client: AsyncClient) -> None:
    """Test history endpoint with limit parameter."""
    response = await client.get("/api/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 10


@pytest.mark.asyncio
async def test_get_plan_by_id_not_found(client: AsyncClient) -> None:
    """Test retrieving non-existent plan by ID."""
    response = await client.get("/api/history/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_plan_route_streaming(
    client: AsyncClient,
    mock_claude_service: ClaudeService,
) -> None:
    """Test route planning endpoint with SSE streaming.

    Args:
        client: Test HTTP client.
        mock_claude_service: Mocked Claude service.
    """
    # Mock Claude streaming response
    async def mock_stream(*args, **kwargs):
        yield "ルート"
        yield "分析"
        yield "結果"

    mock_claude_service.analyze_route_streaming = mock_stream

    # Create plan request
    request_data = {
        "origin": {"lat": 34.573, "lng": 135.483, "name": "堺市上野芝"},
        "destination": {"lat": 34.396, "lng": 135.757, "name": "吉野山"},
        "preferences": {
            "difficulty": "moderate",
            "avoid_traffic": True,
            "prefer_scenic": True,
            "max_distance_km": 100,
            "max_elevation_gain_m": 1500,
        },
        "departure_time": "2025-03-15T07:00:00",
    }

    response = await client.post(
        "/api/plan",
        json=request_data,
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse SSE events
    events = []
    for line in response.text.split("\n\n"):
        if line.strip():
            events.append(line)

    # Should have route_data, weather, token(s), and done events
    assert len(events) >= 4

    # Check event types
    event_types = [e.split("\n")[0].replace("event: ", "") for e in events if e.startswith("event:")]
    assert "route_data" in event_types
    assert "weather" in event_types
    assert "token" in event_types
    assert "done" in event_types


@pytest.mark.asyncio
async def test_plan_request_validation(client: AsyncClient) -> None:
    """Test plan request with invalid data."""
    # Missing required fields
    response = await client.post(
        "/api/plan",
        json={"origin": {"lat": 34.573, "lng": 135.483}},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_plan_request_invalid_coords(client: AsyncClient) -> None:
    """Test plan request with invalid coordinates."""
    request_data = {
        "origin": {"lat": 999, "lng": 135.483},  # Invalid latitude
        "destination": {"lat": 34.396, "lng": 135.757},
        "preferences": {
            "difficulty": "moderate",
            "avoid_traffic": True,
            "prefer_scenic": True,
        },
        "departure_time": "2025-03-15T07:00:00",
    }

    response = await client.post("/api/plan", json=request_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_plan_request_invalid_difficulty(client: AsyncClient) -> None:
    """Test plan request with invalid difficulty level."""
    request_data = {
        "origin": {"lat": 34.573, "lng": 135.483},
        "destination": {"lat": 34.396, "lng": 135.757},
        "preferences": {
            "difficulty": "invalid",  # Should be easy/moderate/hard
            "avoid_traffic": True,
            "prefer_scenic": True,
        },
        "departure_time": "2025-03-15T07:00:00",
    }

    response = await client.post("/api/plan", json=request_data)
    assert response.status_code == 422
