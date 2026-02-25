"""Data models for the Cycling Route Planner API.

This module defines all Pydantic models used across the application.
Other teams should import these models as read-only references.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location with coordinates and optional name."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lng: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    name: str | None = Field(None, description="Human-readable location name")


class RoutePreferences(BaseModel):
    """User preferences for route planning."""

    difficulty: Literal["easy", "moderate", "hard"] = Field(
        ..., description="Desired route difficulty level"
    )
    avoid_traffic: bool = Field(True, description="Avoid high-traffic roads")
    prefer_scenic: bool = Field(True, description="Prefer scenic routes")
    max_distance_km: float | None = Field(
        None, ge=0, description="Maximum route distance in kilometers"
    )
    max_elevation_gain_m: float | None = Field(
        None, ge=0, description="Maximum total elevation gain in meters"
    )


class PlanRequest(BaseModel):
    """Request payload for route planning."""

    origin: Location = Field(..., description="Starting point")
    destination: Location = Field(..., description="Destination point")
    preferences: RoutePreferences = Field(..., description="Route preferences")
    departure_time: datetime = Field(..., description="Planned departure time")


class RouteSegment(BaseModel):
    """A segment of the complete route."""

    coordinates: list[tuple[float, float]] = Field(
        ..., description="List of (lat, lng) coordinate pairs"
    )
    elevations: list[float] | None = Field(
        None, description="Elevation in meters for each coordinate point"
    )
    distance_km: float = Field(..., ge=0, description="Segment distance in kilometers")
    elevation_gain_m: float = Field(
        ..., ge=0, description="Total elevation gain in meters"
    )
    elevation_loss_m: float = Field(
        ..., ge=0, description="Total elevation loss in meters"
    )
    estimated_duration_min: int = Field(
        ..., ge=0, description="Estimated duration in minutes"
    )
    surface_type: Literal["paved", "gravel", "dirt"] = Field(
        ..., description="Road surface type"
    )


class WeatherForecast(BaseModel):
    """Weather forecast for a specific time and location."""

    time: datetime = Field(..., description="Forecast timestamp")
    temperature: float = Field(..., description="Temperature in Celsius")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    wind_direction: float = Field(
        ..., ge=0, le=360, description="Wind direction in degrees"
    )
    precipitation_probability: float = Field(
        ..., ge=0, le=100, description="Precipitation probability percentage"
    )
    weather_code: int = Field(..., description="WMO weather code")
    description: str = Field(..., description="Human-readable weather description")


class RoutePlan(BaseModel):
    """Complete route plan with analysis."""

    id: str = Field(..., description="Unique plan identifier")
    segments: list[RouteSegment] = Field(..., description="Route segments")
    total_distance_km: float = Field(
        ..., ge=0, description="Total route distance in kilometers"
    )
    total_elevation_gain_m: float = Field(
        ..., ge=0, description="Total elevation gain in meters"
    )
    total_duration_min: int = Field(
        ..., ge=0, description="Estimated total duration in minutes"
    )
    weather_forecasts: list[WeatherForecast] = Field(
        ..., description="Weather forecasts along the route"
    )
    llm_analysis: str = Field(..., description="LLM-generated route analysis and advice")
    warnings: list[str] = Field(
        default_factory=list,
        description="Important warnings (e.g., strong winds, rain)",
    )
    recommended_gear: list[str] = Field(
        default_factory=list, description="Recommended equipment and gear"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Plan creation timestamp"
    )


class WeatherResponse(BaseModel):
    """Response wrapper for weather data."""

    data: WeatherForecast


class ElevationPoint(BaseModel):
    """Elevation data for a point along the route."""

    distance_km: float = Field(..., ge=0, description="Distance from start in kilometers")
    elevation_m: float = Field(..., description="Elevation in meters")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")


class ElevationProfile(BaseModel):
    """Elevation profile for the entire route."""

    points: list[ElevationPoint] = Field(..., description="Elevation data points")
    total_gain_m: float = Field(..., ge=0, description="Total elevation gain in meters")
    total_loss_m: float = Field(..., ge=0, description="Total elevation loss in meters")
    max_elevation_m: float = Field(..., description="Maximum elevation in meters")
    min_elevation_m: float = Field(..., description="Minimum elevation in meters")


class ElevationResponse(BaseModel):
    """Response wrapper for elevation data."""

    data: ElevationProfile


class HistoryResponse(BaseModel):
    """Response wrapper for route history."""

    data: list[RoutePlan]


class GeocodeResponse(BaseModel):
    """Response wrapper for geocoding results."""

    data: list[Location] = Field(..., description="List of matching locations")
