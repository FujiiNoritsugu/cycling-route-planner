"""Weather forecast API endpoint.

This module provides the GET /api/weather endpoint for retrieving
weather forecasts at specific locations and times.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ..schemas import WeatherForecast, WeatherResponse

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    date: str = Query(..., description="Date in ISO format (YYYY-MM-DD)"),
) -> WeatherResponse:
    """Get weather forecast for a specific location and date.

    This endpoint will use the planner.weather_client module
    (to be implemented by the route-planner agent).

    Args:
        lat: Latitude in degrees.
        lng: Longitude in degrees.
        date: Date string in ISO format.

    Returns:
        WeatherResponse with forecast data.

    Raises:
        HTTPException: If date format is invalid or weather service fails.
    """
    try:
        # Parse date
        forecast_date = datetime.fromisoformat(date)
    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date}. Use ISO format (YYYY-MM-DD).",
        ) from err

    try:
        # TODO: Replace with actual planner module call:
        # from planner import weather_client
        # forecast = await weather_client.get_forecast(lat, lng, forecast_date)

        # Mock implementation
        forecast = await _mock_get_weather_forecast(lat, lng, forecast_date)

        return WeatherResponse(data=forecast)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch weather data: {str(e)}",
        ) from e


async def _mock_get_weather_forecast(
    lat: float, lng: float, date: datetime
) -> WeatherForecast:
    """Mock weather forecast retrieval.

    This will be replaced by the actual planner.weather_client implementation.

    Args:
        lat: Latitude.
        lng: Longitude.
        date: Forecast date.

    Returns:
        Mock WeatherForecast.
    """
    # Return mock data
    return WeatherForecast(
        time=date,
        temperature=20.0,
        wind_speed=4.0,
        wind_direction=135.0,
        precipitation_probability=15.0,
        weather_code=1,
        description="晴れ時々曇り",
    )
