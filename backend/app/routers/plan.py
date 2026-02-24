"""Route planning API endpoint.

This module provides the POST /api/plan endpoint for generating
cycling route plans with LLM analysis via SSE streaming.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from planner import RouteGenerator

from ..database import save_route_plan
from ..schemas import (
    PlanRequest,
    RoutePlan,
    RouteSegment,
    WeatherForecast,
)
from ..services.claude import ClaudeService, get_claude_service
from ..services.streaming import format_sse, stream_error

router = APIRouter(prefix="/api", tags=["planning"])


@router.post("/plan")
async def plan_route(
    request: PlanRequest,
    claude_service: ClaudeService = Depends(get_claude_service),
) -> StreamingResponse:
    """Generate cycling route plan with LLM analysis.

    This endpoint streams results via Server-Sent Events (SSE):
    - event: route_data -> Route coordinates and elevation
    - event: weather -> Weather forecasts
    - event: token -> LLM analysis text (streaming)
    - event: done -> Completion signal

    Args:
        request: Route planning request with origin, destination, and preferences.
        claude_service: Injected Claude API service.

    Returns:
        StreamingResponse with SSE events.
    """

    async def generate_stream() -> AsyncIterator[str]:
        try:
            # Initialize route generator
            route_generator = RouteGenerator()

            # Convert backend schemas to planner schemas for compatibility
            from planner.schemas import Location as PlannerLocation
            from planner.schemas import RoutePreferences as PlannerPreferences

            planner_origin = PlannerLocation(
                lat=request.origin.lat,
                lng=request.origin.lng,
                name=request.origin.name,
            )
            planner_dest = PlannerLocation(
                lat=request.destination.lat,
                lng=request.destination.lng,
                name=request.destination.name,
            )
            planner_prefs = PlannerPreferences(
                difficulty=request.preferences.difficulty,
                avoid_traffic=request.preferences.avoid_traffic,
                prefer_scenic=request.preferences.prefer_scenic,
                max_distance_km=request.preferences.max_distance_km,
                max_elevation_gain_m=request.preferences.max_elevation_gain_m,
            )

            # Generate route using real OpenRouteService API
            planner_segments = await route_generator.generate_route(
                origin=planner_origin,
                destination=planner_dest,
                preferences=planner_prefs,
            )

            # Convert planner segments back to backend schema
            segments = [
                RouteSegment(
                    coordinates=seg.coordinates,
                    distance_km=seg.distance_km,
                    elevation_gain_m=seg.elevation_gain_m,
                    elevation_loss_m=seg.elevation_loss_m,
                    estimated_duration_min=seg.estimated_duration_min,
                    surface_type=seg.surface_type,
                )
                for seg in planner_segments
            ]

            # Mock weather for now (will be replaced with real weather client later)
            weather_forecasts = await _mock_get_weather(request)

            # Calculate totals
            total_distance_km = sum(seg.distance_km for seg in segments)
            total_elevation_gain_m = sum(seg.elevation_gain_m for seg in segments)
            total_duration_min = sum(seg.estimated_duration_min for seg in segments)

            # Send route data
            route_data = {
                "segments": [seg.model_dump() for seg in segments],
                "total_distance_km": total_distance_km,
                "total_elevation_gain_m": total_elevation_gain_m,
                "total_duration_min": total_duration_min,
            }
            yield format_sse("route_data", route_data)

            # Send weather data
            weather_data = [w.model_dump() for w in weather_forecasts]
            yield format_sse("weather", weather_data)

            # Stream LLM analysis
            llm_analysis_parts: list[str] = []
            async for token in claude_service.analyze_route_streaming(
                segments=segments,
                weather_forecasts=weather_forecasts,
                total_distance_km=total_distance_km,
                total_elevation_gain_m=total_elevation_gain_m,
                difficulty=request.preferences.difficulty,
            ):
                llm_analysis_parts.append(token)
                yield format_sse("token", token)

            # Combine full LLM analysis
            llm_analysis = "".join(llm_analysis_parts)

            # Extract warnings and gear recommendations from LLM analysis
            # Simple heuristic-based extraction (can be enhanced)
            warnings = _extract_warnings(llm_analysis, weather_forecasts)
            recommended_gear = _extract_gear_recommendations(llm_analysis)

            # Create and save route plan
            plan = RoutePlan(
                id=str(uuid.uuid4()),
                segments=segments,
                total_distance_km=total_distance_km,
                total_elevation_gain_m=total_elevation_gain_m,
                total_duration_min=total_duration_min,
                weather_forecasts=weather_forecasts,
                llm_analysis=llm_analysis,
                warnings=warnings,
                recommended_gear=recommended_gear,
                created_at=datetime.now(),
            )

            # Save to database
            save_route_plan(plan)

            # Send completion
            yield format_sse("done", {"status": "complete", "plan_id": plan.id})

        except Exception as e:
            # Stream error
            async for event in stream_error(str(e)):
                yield event

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def _mock_get_weather(request: PlanRequest) -> list[WeatherForecast]:
    """Mock weather forecast (to be replaced by planner module).

    Args:
        request: Route planning request.

    Returns:
        List of weather forecasts.
    """
    # Mock forecast at departure time
    forecast = WeatherForecast(
        time=request.departure_time,
        temperature=18.0,
        wind_speed=3.5,
        wind_direction=180.0,
        precipitation_probability=10.0,
        weather_code=1,
        description="晴れ",
    )

    return [forecast]


def _extract_warnings(analysis: str, forecasts: list[WeatherForecast]) -> list[str]:
    """Extract warnings from LLM analysis and weather data.

    Args:
        analysis: LLM analysis text.
        forecasts: Weather forecasts.

    Returns:
        List of warning messages.
    """
    warnings = []

    # Check for high winds
    max_wind = max((f.wind_speed for f in forecasts), default=0)
    if max_wind > 10:
        warnings.append(f"強風警告: 最大風速{max_wind:.1f}m/s")

    # Check for rain
    max_precip = max((f.precipitation_probability for f in forecasts), default=0)
    if max_precip > 50:
        warnings.append(f"降雨注意: 降水確率{max_precip:.0f}%")

    # Check for high temperature
    max_temp = max((f.temperature for f in forecasts), default=0)
    if max_temp > 30:
        warnings.append(f"熱中症注意: 最高気温{max_temp:.1f}°C")

    # Low temperature
    min_temp = min((f.temperature for f in forecasts), default=100)
    if min_temp < 5:
        warnings.append(f"低温注意: 最低気温{min_temp:.1f}°C")

    return warnings


def _extract_gear_recommendations(analysis: str) -> list[str]:
    """Extract gear recommendations from LLM analysis.

    Args:
        analysis: LLM analysis text.

    Returns:
        List of recommended gear.
    """
    # Basic gear recommendations (can be enhanced with NLP)
    gear = ["ヘルメット", "グローブ", "補給食", "水分"]

    # Add conditional gear based on keywords in analysis
    if "雨" in analysis or "降水" in analysis:
        gear.extend(["レインウェア", "防水バッグ"])

    if "寒" in analysis or "低温" in analysis:
        gear.extend(["ウィンドブレーカー", "アームウォーマー"])

    if "暑" in analysis or "高温" in analysis:
        gear.append("日焼け止め")

    if "風" in analysis:
        gear.append("アイウェア")

    return gear
