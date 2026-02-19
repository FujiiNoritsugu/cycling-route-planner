"""Pytest configuration and fixtures for planner tests."""

import pytest
from datetime import datetime
from planner.schemas import Location, RoutePreferences, RouteSegment, WeatherForecast


@pytest.fixture
def sample_location_origin():
    """Sample origin location (Sakai, Osaka)."""
    return Location(lat=34.573, lng=135.483, name="Sakai City")


@pytest.fixture
def sample_location_destination():
    """Sample destination location (Yoshino)."""
    return Location(lat=34.396, lng=135.757, name="Yoshino Mountain")


@pytest.fixture
def sample_preferences():
    """Sample route preferences."""
    return RoutePreferences(
        difficulty="moderate",
        avoid_traffic=True,
        prefer_scenic=True,
        max_distance_km=100.0,
        max_elevation_gain_m=1500.0,
    )


@pytest.fixture
def sample_route_segment():
    """Sample route segment."""
    return RouteSegment(
        coordinates=[(34.573, 135.483), (34.550, 135.500), (34.520, 135.520)],
        distance_km=15.5,
        elevation_gain_m=250.0,
        elevation_loss_m=50.0,
        estimated_duration_min=60,
        surface_type="paved",
    )


@pytest.fixture
def sample_route_segments():
    """Sample list of route segments."""
    return [
        RouteSegment(
            coordinates=[(34.573, 135.483), (34.550, 135.500)],
            distance_km=10.0,
            elevation_gain_m=100.0,
            elevation_loss_m=20.0,
            estimated_duration_min=40,
            surface_type="paved",
        ),
        RouteSegment(
            coordinates=[(34.550, 135.500), (34.520, 135.600)],
            distance_km=15.0,
            elevation_gain_m=300.0,
            elevation_loss_m=50.0,
            estimated_duration_min=75,
            surface_type="gravel",
        ),
        RouteSegment(
            coordinates=[(34.520, 135.600), (34.396, 135.757)],
            distance_km=25.0,
            elevation_gain_m=500.0,
            elevation_loss_m=100.0,
            estimated_duration_min=120,
            surface_type="paved",
        ),
    ]


@pytest.fixture
def sample_weather_forecast():
    """Sample weather forecast."""
    return WeatherForecast(
        time=datetime(2025, 3, 15, 8, 0),
        temperature=15.0,
        wind_speed=5.0,
        wind_direction=180.0,
        precipitation_probability=20.0,
        weather_code=1,
        description="Mainly clear",
    )


@pytest.fixture
def sample_weather_forecasts():
    """Sample list of weather forecasts."""
    return [
        WeatherForecast(
            time=datetime(2025, 3, 15, 7, 0),
            temperature=12.0,
            wind_speed=4.0,
            wind_direction=180.0,
            precipitation_probability=10.0,
            weather_code=0,
            description="Clear sky",
        ),
        WeatherForecast(
            time=datetime(2025, 3, 15, 10, 0),
            temperature=18.0,
            wind_speed=6.0,
            wind_direction=190.0,
            precipitation_probability=15.0,
            weather_code=1,
            description="Mainly clear",
        ),
        WeatherForecast(
            time=datetime(2025, 3, 15, 13, 0),
            temperature=22.0,
            wind_speed=8.0,
            wind_direction=200.0,
            precipitation_probability=25.0,
            weather_code=2,
            description="Partly cloudy",
        ),
    ]


@pytest.fixture
def sample_elevation_profile():
    """Sample elevation profile."""
    return [100.0, 120.0, 150.0, 200.0, 280.0, 350.0, 420.0, 450.0, 480.0, 500.0]
