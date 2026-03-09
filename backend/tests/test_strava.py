"""Tests for Strava integration service and API endpoints.

Tests cover the StravaService fitness profile builder and API endpoints
with mocked external Strava API calls.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.strava import StravaService


@pytest.fixture
async def client() -> AsyncClient:
    """Create async HTTP client for testing.

    Yields:
        Configured AsyncClient.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestBuildFitnessProfile:
    """Tests for StravaService.build_fitness_profile method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = StravaService()

    def test_no_activities(self) -> None:
        """Empty activity list returns has_data=False."""
        result = self.service.build_fitness_profile([])
        assert result["has_data"] is False
        assert "message" in result

    def test_no_cycling_activities(self) -> None:
        """Non-cycling activities are filtered out."""
        activities = [
            {"type": "Run", "distance": 10000, "average_speed": 3.0},
            {"type": "Swim", "distance": 2000, "average_speed": 1.5},
        ]
        result = self.service.build_fitness_profile(activities)
        assert result["has_data"] is False

    def test_beginner_profile(self) -> None:
        """Short, flat rides classify as beginner."""
        activities = [
            {
                "type": "Ride",
                "distance": 20000,  # 20km
                "average_speed": 5.0,  # 18 km/h
                "total_elevation_gain": 100,
                "moving_time": 3600,  # 60 min
                "start_date_local": "2026-02-15T09:00:00Z",
            },
            {
                "type": "Ride",
                "distance": 25000,  # 25km
                "average_speed": 5.5,
                "total_elevation_gain": 150,
                "moving_time": 4200,
                "start_date_local": "2026-02-20T10:00:00Z",
            },
        ]
        result = self.service.build_fitness_profile(activities)
        assert result["has_data"] is True
        assert result["fitness_level"] == "beginner"
        assert result["total_activities"] == 2
        assert result["avg_distance_km"] == 22.5

    def test_intermediate_profile(self) -> None:
        """Moderate rides with regular frequency classify as intermediate."""
        activities = []
        # Create 26 rides across ~90 days (2+/week)
        # Spread across Jan and Feb 2026
        for i in range(26):
            day = 1 + (i % 28)
            month = 1 if i < 14 else 2
            activities.append(
                {
                    "type": "Ride",
                    "distance": 50000,  # 50km
                    "average_speed": 7.0,  # 25.2 km/h
                    "total_elevation_gain": 500,
                    "moving_time": 7200,
                    "start_date_local": f"2026-{month:02d}-{day:02d}T08:00:00Z",
                }
            )
        result = self.service.build_fitness_profile(activities)
        assert result["has_data"] is True
        assert result["fitness_level"] == "intermediate"

    def test_advanced_profile(self) -> None:
        """Long, hilly rides with high frequency classify as advanced."""
        activities = []
        # Create 40 rides spread across ~90 days (3+/week)
        for i in range(40):
            day = 1 + (i % 28)
            # Spread across Jan-Mar 2026
            if i < 28:
                month = 1
            elif i < 56:
                month = 2
            else:
                month = 3
            activities.append(
                {
                    "type": "Ride",
                    "distance": 100000,  # 100km
                    "average_speed": 8.5,  # 30.6 km/h
                    "total_elevation_gain": 1200,
                    "moving_time": 14400,
                    "start_date_local": f"2026-{month:02d}-{day:02d}T06:00:00Z",
                }
            )
        result = self.service.build_fitness_profile(activities)
        assert result["has_data"] is True
        assert result["fitness_level"] == "advanced"
        assert result["avg_distance_km"] == 100.0

    def test_mixed_activity_types(self) -> None:
        """Only cycling activities are included in profile."""
        activities = [
            {
                "type": "Ride",
                "distance": 30000,
                "average_speed": 6.0,
                "total_elevation_gain": 200,
                "moving_time": 5400,
                "start_date_local": "2026-02-10T09:00:00Z",
            },
            {
                "type": "Run",
                "distance": 10000,
                "average_speed": 3.0,
                "total_elevation_gain": 50,
                "moving_time": 3000,
                "start_date_local": "2026-02-11T09:00:00Z",
            },
            {
                "type": "VirtualRide",
                "distance": 40000,
                "average_speed": 7.0,
                "total_elevation_gain": 300,
                "moving_time": 5400,
                "start_date_local": "2026-02-12T09:00:00Z",
            },
        ]
        result = self.service.build_fitness_profile(activities)
        assert result["has_data"] is True
        assert result["total_activities"] == 2  # Only Ride + VirtualRide

    def test_ebike_rides_included(self) -> None:
        """EBikeRide activities are included in the profile."""
        activities = [
            {
                "type": "EBikeRide",
                "distance": 35000,
                "average_speed": 6.5,
                "total_elevation_gain": 250,
                "moving_time": 5000,
                "start_date_local": "2026-02-15T10:00:00Z",
            },
        ]
        result = self.service.build_fitness_profile(activities)
        assert result["has_data"] is True
        assert result["total_activities"] == 1


class TestStravaAuthEndpoint:
    """Tests for Strava auth URL endpoint."""

    @pytest.mark.asyncio
    async def test_get_auth_url_without_client_id(
        self, client: AsyncClient
    ) -> None:
        """Missing STRAVA_CLIENT_ID returns 500."""
        with patch.dict("os.environ", {"STRAVA_CLIENT_ID": ""}, clear=False):
            response = await client.get("/api/strava/auth-url")
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_auth_url_with_client_id(
        self, client: AsyncClient
    ) -> None:
        """Valid STRAVA_CLIENT_ID returns authorization URL."""
        with patch.dict(
            "os.environ", {"STRAVA_CLIENT_ID": "12345"}, clear=False
        ):
            response = await client.get("/api/strava/auth-url")
            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert "client_id=12345" in data["url"]
            assert "scope=read,activity:read" in data["url"]


class TestStravaProfileEndpoint:
    """Tests for Strava fitness profile endpoint."""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, client: AsyncClient) -> None:
        """Successful profile fetch returns fitness data."""
        mock_activities = [
            {
                "type": "Ride",
                "distance": 30000,
                "average_speed": 6.0,
                "total_elevation_gain": 200,
                "moving_time": 5400,
                "start_date_local": "2026-02-10T09:00:00Z",
            },
        ]
        with patch.object(
            StravaService,
            "get_activities",
            new_callable=AsyncMock,
            return_value=mock_activities,
        ):
            response = await client.get(
                "/api/strava/profile",
                params={"access_token": "mock-token"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["has_data"] is True
            assert data["fitness_level"] == "beginner"
            assert data["total_activities"] == 1

    @pytest.mark.asyncio
    async def test_get_profile_api_error(self, client: AsyncClient) -> None:
        """API error returns 400."""
        with patch.object(
            StravaService,
            "get_activities",
            new_callable=AsyncMock,
            side_effect=Exception("API error"),
        ):
            response = await client.get(
                "/api/strava/profile",
                params={"access_token": "bad-token"},
            )
            assert response.status_code == 400
