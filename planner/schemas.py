"""Data models for the cycling route planner.

This module defines Pydantic models that will eventually be replaced by
importing from backend.app.schemas once it's available.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location."""

    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    name: str | None = Field(None, description="Location name")


class RoutePreferences(BaseModel):
    """User preferences for route generation."""

    difficulty: str = Field(..., description="easy | moderate | hard")
    avoid_traffic: bool = Field(True, description="Avoid high traffic areas")
    prefer_scenic: bool = Field(True, description="Prefer scenic routes")
    max_distance_km: float | None = Field(None, description="Maximum distance in km")
    max_elevation_gain_m: float | None = Field(
        None, description="Maximum elevation gain in meters"
    )


class PlanRequest(BaseModel):
    """Request for route planning."""

    origin: Location
    destination: Location
    preferences: RoutePreferences
    departure_time: datetime


class RouteSegment(BaseModel):
    """A segment of a cycling route."""

    coordinates: list[tuple[float, float]] = Field(
        ..., description="List of (lat, lng) coordinates"
    )
    elevations: list[float] | None = Field(
        None, description="Elevation in meters for each coordinate point"
    )
    distance_km: float = Field(..., description="Distance in kilometers")
    elevation_gain_m: float = Field(..., description="Elevation gain in meters")
    elevation_loss_m: float = Field(..., description="Elevation loss in meters")
    estimated_duration_min: int = Field(..., description="Estimated duration in minutes")
    surface_type: str = Field(..., description="paved | gravel | dirt")


class WeatherForecast(BaseModel):
    """Weather forecast for a specific time."""

    time: datetime
    temperature: float = Field(..., description="Temperature in Celsius")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    wind_direction: float = Field(..., description="Wind direction in degrees")
    precipitation_probability: float = Field(
        ..., description="Precipitation probability (0-100)"
    )
    weather_code: int = Field(..., description="WMO weather code")
    description: str = Field(..., description="Human-readable weather description")


class RoutePlan(BaseModel):
    """Complete route plan with analysis."""

    id: str
    segments: list[RouteSegment]
    total_distance_km: float
    total_elevation_gain_m: float
    total_duration_min: int
    weather_forecasts: list[WeatherForecast]
    llm_analysis: str = Field(..., description="LLM analysis and advice")
    warnings: list[str] = Field(..., description="Warnings (wind, rain, etc.)")
    recommended_gear: list[str] = Field(..., description="Recommended equipment")
    created_at: datetime
