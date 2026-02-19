"""Tests for route_generator module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from planner.route_generator import RouteGenerator, RouteGenerationError
from planner.schemas import Location, RoutePreferences


@pytest.fixture
def route_generator():
    """Create a RouteGenerator instance with mock API key."""
    return RouteGenerator(api_key="test_api_key")


@pytest.fixture
def mock_ors_response():
    """Mock OpenRouteService API response."""
    return {
        "features": [
            {
                "geometry": {
                    "coordinates": [
                        [135.483, 34.573],
                        [135.500, 34.550],
                        [135.757, 34.396],
                    ]
                },
                "properties": {
                    "summary": {
                        "distance": 50000,  # meters
                        "duration": 7200,  # seconds
                    },
                    "ascent": 800.0,
                    "descent": 200.0,
                    "segments": [
                        {
                            "distance": 50000,
                            "duration": 7200,
                            "ascent": 800.0,
                            "descent": 200.0,
                            "steps": [],
                        }
                    ],
                    "extras": {
                        "surface": {
                            "values": [[0, 10, 1]],  # Paved
                        }
                    },
                },
            }
        ]
    }


class TestRouteGenerator:
    """Tests for RouteGenerator class."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        generator = RouteGenerator(api_key="test_key")
        assert generator.api_key == "test_key"

    def test_init_with_env_var(self, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("ORS_API_KEY", "env_key")
        generator = RouteGenerator()
        assert generator.api_key == "env_key"

    def test_init_without_api_key(self, monkeypatch):
        """Test initialization fails without API key."""
        monkeypatch.delenv("ORS_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenRouteService API key required"):
            RouteGenerator()

    @pytest.mark.asyncio
    async def test_generate_route_success(
        self,
        route_generator,
        sample_location_origin,
        sample_location_destination,
        sample_preferences,
        mock_ors_response,
    ):
        """Test successful route generation."""
        with patch("httpx.AsyncClient.post") as mock_post:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_ors_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            segments = await route_generator.generate_route(
                sample_location_origin, sample_location_destination, sample_preferences
            )

            assert len(segments) > 0
            assert segments[0].distance_km == 50.0
            assert segments[0].elevation_gain_m == 800.0
            assert segments[0].surface_type in ["paved", "gravel", "dirt"]

    @pytest.mark.asyncio
    async def test_generate_route_api_error(
        self,
        route_generator,
        sample_location_origin,
        sample_location_destination,
        sample_preferences,
    ):
        """Test route generation with API error."""
        with patch("httpx.AsyncClient.post") as mock_post:
            # Mock API error
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_response
            )

            with pytest.raises(RouteGenerationError, match="OpenRouteService API error"):
                await route_generator.generate_route(
                    sample_location_origin,
                    sample_location_destination,
                    sample_preferences,
                )

    @pytest.mark.asyncio
    async def test_generate_route_network_error(
        self,
        route_generator,
        sample_location_origin,
        sample_location_destination,
        sample_preferences,
    ):
        """Test route generation with network error."""
        with patch("httpx.AsyncClient.post") as mock_post:
            # Mock network error
            mock_post.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(
                RouteGenerationError, match="Failed to connect to OpenRouteService"
            ):
                await route_generator.generate_route(
                    sample_location_origin,
                    sample_location_destination,
                    sample_preferences,
                )

    def test_determine_preference_scenic(self, route_generator):
        """Test preference determination for scenic routes."""
        prefs = RoutePreferences(
            difficulty="moderate",
            avoid_traffic=True,
            prefer_scenic=True,
        )
        assert route_generator._determine_preference(prefs) == "recommended"

    def test_determine_preference_easy(self, route_generator):
        """Test preference determination for easy routes."""
        prefs = RoutePreferences(
            difficulty="easy",
            avoid_traffic=True,
            prefer_scenic=False,
        )
        assert route_generator._determine_preference(prefs) == "shortest"

    def test_determine_preference_fastest(self, route_generator):
        """Test preference determination for fastest routes."""
        prefs = RoutePreferences(
            difficulty="hard",
            avoid_traffic=False,
            prefer_scenic=False,
        )
        assert route_generator._determine_preference(prefs) == "fastest"

    def test_estimate_surface_type_paved(self, route_generator, sample_preferences):
        """Test surface type estimation for paved surfaces."""
        properties = {
            "extras": {
                "surface": {
                    "values": [[0, 10, 1]],  # Paved code
                }
            }
        }
        surface = route_generator._estimate_surface_type(properties, sample_preferences)
        assert surface == "paved"

    def test_estimate_surface_type_unpaved(self, route_generator, sample_preferences):
        """Test surface type estimation for unpaved surfaces."""
        properties = {
            "extras": {
                "surface": {
                    "values": [[0, 10, 2]],  # Unpaved code
                }
            }
        }
        surface = route_generator._estimate_surface_type(properties, sample_preferences)
        assert surface == "gravel"

    def test_estimate_surface_type_fallback_hard(self, route_generator):
        """Test surface type fallback for hard difficulty."""
        properties = {}
        prefs = RoutePreferences(
            difficulty="hard",
            avoid_traffic=False,
            prefer_scenic=False,
        )
        surface = route_generator._estimate_surface_type(properties, prefs)
        assert surface == "gravel"

    def test_estimate_surface_type_fallback_easy(self, route_generator):
        """Test surface type fallback for easy difficulty."""
        properties = {}
        prefs = RoutePreferences(
            difficulty="easy",
            avoid_traffic=False,
            prefer_scenic=False,
        )
        surface = route_generator._estimate_surface_type(properties, prefs)
        assert surface == "paved"
