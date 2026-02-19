"""Server-Sent Events (SSE) streaming utilities.

This module provides helpers for streaming route planning results
to the frontend using SSE format.
"""

import json
from collections.abc import AsyncIterator
from typing import Any


def format_sse(event: str, data: Any) -> str:
    """Format data as Server-Sent Events message.

    Args:
        event: Event type name.
        data: Data payload (will be JSON-serialized if not a string).

    Returns:
        Formatted SSE message string.
    """
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, default=str)

    return f"event: {event}\ndata: {data}\n\n"


async def stream_route_planning(
    route_data: dict[str, Any],
    weather_data: list[dict[str, Any]],
    llm_stream: AsyncIterator[str],
) -> AsyncIterator[str]:
    """Stream route planning results as SSE.

    This function orchestrates the streaming of route data, weather forecasts,
    and LLM analysis in SSE format.

    Args:
        route_data: Route segments and elevation data.
        weather_data: Weather forecasts along the route.
        llm_stream: Async iterator of LLM text chunks.

    Yields:
        SSE-formatted messages.
    """
    # Send route data first
    yield format_sse("route_data", route_data)

    # Send weather data
    yield format_sse("weather", weather_data)

    # Stream LLM analysis tokens
    async for token in llm_stream:
        yield format_sse("token", token)

    # Send completion event
    yield format_sse("done", {"status": "complete"})


async def stream_error(error_message: str) -> AsyncIterator[str]:
    """Stream error message as SSE.

    Args:
        error_message: Error message to send.

    Yields:
        SSE-formatted error message.
    """
    yield format_sse("error", {"message": error_message})
    yield format_sse("done", {"status": "error"})
