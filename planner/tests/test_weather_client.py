"""Tests for weather_client module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import httpx
from planner.weather_client import WeatherClient, WeatherAPIError
from planner.schemas import Location


@pytest.fixture
def weather_client():
    """Create a WeatherClient instance."""
    return WeatherClient()


@pytest.fixture
def mock_openmeteo_response():
    """Mock OpenMeteo API response."""
    return {
        "hourly": {
            "time": [
                "2025-03-15T07:00:00Z",
                "2025-03-15T08:00:00Z",
                "2025-03-15T09:00:00Z",
                "2025-03-15T10:00:00Z",
            ],
            "temperature_2m": [12.0, 14.0, 16.0, 18.0],
            "wind_speed_10m": [4.0, 5.0, 6.0, 7.0],
            "wind_direction_10m": [180.0, 185.0, 190.0, 195.0],
            "precipitation_probability": [10.0, 15.0, 20.0, 25.0],
            "weather_code": [0, 1, 1, 2],
        }
    }


class TestWeatherClient:
    """Tests for WeatherClient class."""

    @pytest.mark.asyncio
    async def test_get_forecast_success(
        self, weather_client, sample_location_origin, mock_openmeteo_response
    ):
        """Test successful weather forecast retrieval."""
        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openmeteo_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            start_time = datetime(2025, 3, 15, 7, 0)
            forecasts = await weather_client.get_forecast(
                sample_location_origin, start_time, hours=4
            )

            assert len(forecasts) == 4
            assert forecasts[0].temperature == 12.0
            assert forecasts[0].wind_speed == 4.0
            assert forecasts[0].weather_code == 0
            assert forecasts[0].description == "Clear sky"

    @pytest.mark.asyncio
    async def test_get_forecast_api_error(
        self, weather_client, sample_location_origin
    ):
        """Test forecast retrieval with API error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock API error
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_get.return_value = mock_response
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_response
            )

            start_time = datetime(2025, 3, 15, 7, 0)
            with pytest.raises(WeatherAPIError, match="OpenMeteo API error"):
                await weather_client.get_forecast(
                    sample_location_origin, start_time, hours=24
                )

    @pytest.mark.asyncio
    async def test_get_forecast_network_error(
        self, weather_client, sample_location_origin
    ):
        """Test forecast retrieval with network error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock network error
            mock_get.side_effect = httpx.RequestError("Connection failed")

            start_time = datetime(2025, 3, 15, 7, 0)
            with pytest.raises(WeatherAPIError, match="Failed to connect to OpenMeteo"):
                await weather_client.get_forecast(
                    sample_location_origin, start_time, hours=24
                )

    @pytest.mark.asyncio
    async def test_get_route_forecast(
        self, weather_client, mock_openmeteo_response
    ):
        """Test route forecast with multiple locations."""
        locations = [
            Location(lat=34.573, lng=135.483, name="Start"),
            Location(lat=34.500, lng=135.600, name="Middle"),
            Location(lat=34.396, lng=135.757, name="End"),
        ]

        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_openmeteo_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            start_time = datetime(2025, 3, 15, 7, 0)
            forecasts = await weather_client.get_route_forecast(
                locations, start_time, duration_hours=4
            )

            # Should get forecasts for sampled locations
            assert len(forecasts) > 0
            # Forecasts should be sorted by time
            for i in range(len(forecasts) - 1):
                assert forecasts[i].time <= forecasts[i + 1].time

    @pytest.mark.asyncio
    async def test_get_route_forecast_empty_locations(self, weather_client):
        """Test route forecast with empty locations list."""
        start_time = datetime(2025, 3, 15, 7, 0)
        forecasts = await weather_client.get_route_forecast(
            [], start_time, duration_hours=4
        )
        assert forecasts == []

    def test_get_weather_description_clear(self, weather_client):
        """Test weather description for clear sky."""
        description = weather_client._get_weather_description(0)
        assert description == "Clear sky"

    def test_get_weather_description_rain(self, weather_client):
        """Test weather description for rain."""
        description = weather_client._get_weather_description(61)
        assert description == "Slight rain"

    def test_get_weather_description_thunderstorm(self, weather_client):
        """Test weather description for thunderstorm."""
        description = weather_client._get_weather_description(95)
        assert description == "Thunderstorm"

    def test_get_weather_description_unknown(self, weather_client):
        """Test weather description for unknown code."""
        description = weather_client._get_weather_description(999)
        assert "Unknown" in description
        assert "999" in description

    def test_parse_forecast_filters_by_time(
        self, weather_client, mock_openmeteo_response
    ):
        """Test that forecast parsing filters by time range."""
        from datetime import timezone
        start_time = datetime(2025, 3, 15, 7, 0, tzinfo=timezone.utc)
        forecasts = weather_client._parse_forecast(
            mock_openmeteo_response, start_time, hours=2
        )

        # Should only include first 3 hours (7:00, 8:00, 9:00)
        # because end time is 9:00 (7:00 + 2 hours)
        assert len(forecasts) <= 3
        for forecast in forecasts:
            assert forecast.time >= start_time
            assert forecast.time <= start_time + timedelta(hours=2)

    def test_parse_forecast_handles_missing_data(self, weather_client):
        """Test forecast parsing handles missing data gracefully."""
        incomplete_response = {
            "hourly": {
                "time": ["2025-03-15T07:00:00Z"],
                "temperature_2m": [15.0],
                # Missing other fields
            }
        }

        start_time = datetime(2025, 3, 15, 7, 0)
        forecasts = weather_client._parse_forecast(
            incomplete_response, start_time, hours=24
        )

        assert len(forecasts) == 1
        assert forecasts[0].temperature == 15.0
        assert forecasts[0].wind_speed == 0.0  # Default value
        assert forecasts[0].precipitation_probability == 0.0  # Default value
