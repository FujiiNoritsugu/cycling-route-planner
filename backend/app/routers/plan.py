"""Route planning API endpoint.

This module provides the POST /api/plan endpoint for generating
cycling route plans with LLM analysis via SSE streaming.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from planner import RouteGenerator, WeatherClient

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
                is_round_trip=request.preferences.is_round_trip,
            )

            # Generate route(s) using real OpenRouteService API
            if request.preferences.is_round_trip:
                # Generate round trip: outbound + return routes
                segments = await _generate_round_trip_route(
                    route_generator=route_generator,
                    origin=planner_origin,
                    destination=planner_dest,
                    preferences=planner_prefs,
                )
            else:
                # Generate single one-way route
                planner_segments = await route_generator.generate_route(
                    origin=planner_origin,
                    destination=planner_dest,
                    preferences=planner_prefs,
                )
                # Convert planner segments back to backend schema
                segments = [
                    RouteSegment(
                        coordinates=seg.coordinates,
                        elevations=seg.elevations,
                        distance_km=seg.distance_km,
                        elevation_gain_m=seg.elevation_gain_m,
                        elevation_loss_m=seg.elevation_loss_m,
                        estimated_duration_min=seg.estimated_duration_min,
                        surface_type=seg.surface_type,
                        segment_type="outbound",
                    )
                    for seg in planner_segments
                ]

            # Get weather forecasts using real WeatherClient
            weather_forecasts = await _get_route_weather(
                segments=segments,
                departure_time=request.departure_time,
            )

            # Calculate totals
            total_distance_km = sum(seg.distance_km for seg in segments)
            total_elevation_gain_m = sum(seg.elevation_gain_m for seg in segments)
            total_duration_min = sum(seg.estimated_duration_min for seg in segments)

            # Send route data
            route_data = {
                "segments": [seg.model_dump(mode='json') for seg in segments],
                "total_distance_km": total_distance_km,
                "total_elevation_gain_m": total_elevation_gain_m,
                "total_duration_min": total_duration_min,
            }
            yield format_sse("route_data", route_data)

            # Send weather data
            weather_data = [w.model_dump(mode='json') for w in weather_forecasts]
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

            # Save to database (disabled for Cloud Run deployment)
            # save_route_plan(plan)

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


async def _get_route_weather(
    segments: list[RouteSegment],
    departure_time: datetime,
) -> list[WeatherForecast]:
    """Get weather forecasts along the route using OpenMeteo API.

    Args:
        segments: Route segments with coordinates.
        departure_time: Route departure time.

    Returns:
        List of weather forecasts along the route.
    """
    if not segments:
        return []

    # Ensure departure_time is timezone-aware
    from datetime import timezone
    if departure_time.tzinfo is None:
        departure_time = departure_time.replace(tzinfo=timezone.utc)

    # Extract locations from route segments
    from planner.schemas import Location as PlannerLocation

    locations = []
    for segment in segments:
        if segment.coordinates:
            # Sample every 10th coordinate or use all if less than 10
            step = max(1, len(segment.coordinates) // 10)
            for lat, lng in segment.coordinates[::step]:
                locations.append(PlannerLocation(lat=lat, lng=lng))

    if not locations:
        return []

    # Calculate total duration in hours
    total_duration_min = sum(seg.estimated_duration_min for seg in segments)
    duration_hours = max(1, total_duration_min // 60)

    # Get weather forecasts using WeatherClient
    weather_client = WeatherClient()
    planner_forecasts = await weather_client.get_route_forecast(
        locations=locations,
        start_time=departure_time,
        duration_hours=duration_hours,
    )

    # Convert planner WeatherForecast to backend WeatherForecast
    weather_forecasts = [
        WeatherForecast(
            time=f.time,
            temperature=f.temperature,
            wind_speed=f.wind_speed,
            wind_direction=f.wind_direction,
            precipitation_probability=f.precipitation_probability,
            weather_code=f.weather_code,
            description=f.description,
        )
        for f in planner_forecasts
    ]

    return weather_forecasts


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


async def _generate_round_trip_route(
    route_generator: "RouteGenerator",
    origin: "PlannerLocation",
    destination: "PlannerLocation",
    preferences: "PlannerPreferences",
) -> list[RouteSegment]:
    """Generate round trip route with different outbound and return paths.

    Args:
        route_generator: RouteGenerator instance.
        origin: Starting location.
        destination: Destination location.
        preferences: Route preferences.

    Returns:
        List of route segments (outbound + return).
    """
    import logging
    logger = logging.getLogger(__name__)

    # Import here to avoid circular imports
    from planner.schemas import Location as PlannerLocation
    from planner.schemas import RoutePreferences as PlannerPreferences

    # Generate outbound route (origin -> destination)
    outbound_planner_segments = await route_generator.generate_route(
        origin=origin,
        destination=destination,
        preferences=preferences,
    )

    # Collect outbound coordinates for avoidance
    outbound_coords: list[tuple[float, float]] = []
    for seg in outbound_planner_segments:
        outbound_coords.extend(seg.coordinates)

    # Convert outbound segments to backend schema
    outbound_segments = [
        RouteSegment(
            coordinates=seg.coordinates,
            elevations=seg.elevations,
            distance_km=seg.distance_km,
            elevation_gain_m=seg.elevation_gain_m,
            elevation_loss_m=seg.elevation_loss_m,
            estimated_duration_min=seg.estimated_duration_min,
            surface_type=seg.surface_type,
            segment_type="outbound",
        )
        for seg in outbound_planner_segments
    ]

    # Generate return route (destination -> origin), avoiding outbound path
    try:
        return_planner_segments = await route_generator.generate_route(
            origin=destination,
            destination=origin,
            preferences=preferences,
            avoid_coordinates=outbound_coords,
        )
    except Exception as e:
        # Fallback: generate return route without avoidance
        logger.warning(f"Failed to generate alternative return route: {e}")
        logger.info("Falling back to standard return route")
        return_planner_segments = await route_generator.generate_route(
            origin=destination,
            destination=origin,
            preferences=preferences,
        )

    # Convert return segments to backend schema
    return_segments = [
        RouteSegment(
            coordinates=seg.coordinates,
            elevations=seg.elevations,
            distance_km=seg.distance_km,
            elevation_gain_m=seg.elevation_gain_m,
            elevation_loss_m=seg.elevation_loss_m,
            estimated_duration_min=seg.estimated_duration_min,
            surface_type=seg.surface_type,
            segment_type="return",
        )
        for seg in return_planner_segments
    ]

    return outbound_segments + return_segments
