"""Route generation using OpenRouteService API."""

import os
from typing import Literal
import httpx
from planner.schemas import Location, RouteSegment, RoutePreferences


class RouteGenerationError(Exception):
    """Raised when route generation fails."""

    pass


class RouteGenerator:
    """Generates cycling routes using OpenRouteService API."""

    BASE_URL = "https://api.openrouteservice.org/v2/directions"

    def __init__(self, api_key: str | None = None):
        """Initialize the route generator.

        Args:
            api_key: OpenRouteService API key. If None, reads from ORS_API_KEY env var.

        Raises:
            ValueError: If API key is not provided and not in environment.
        """
        self.api_key = api_key or os.getenv("ORS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouteService API key required. Set ORS_API_KEY environment variable."
            )

    async def generate_route(
        self,
        origin: Location,
        destination: Location,
        preferences: RoutePreferences,
        profile: Literal["cycling-regular", "cycling-road", "cycling-mountain"] = "cycling-regular",
    ) -> list[RouteSegment]:
        """Generate a cycling route from origin to destination.

        Args:
            origin: Starting location.
            destination: Ending location.
            preferences: Route preferences.
            profile: Cycling profile (regular, road, mountain).

        Returns:
            List of route segments.

        Raises:
            RouteGenerationError: If route generation fails.
        """
        # Determine preference parameter based on user preferences
        preference = self._determine_preference(preferences)

        # Build request payload
        payload = {
            "coordinates": [[origin.lng, origin.lat], [destination.lng, destination.lat]],
            "preference": preference,
            "elevation": True,
            "instructions": True,
        }

        # Add optional constraints
        # Note: avoid_features for cycling profiles is limited
        # We'll rely on the preference parameter instead

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{profile}/geojson",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            raise RouteGenerationError(
                f"OpenRouteService API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise RouteGenerationError(
                f"Failed to connect to OpenRouteService: {e}"
            ) from e

        # Parse response and create route segments
        return self._parse_response(data, preferences)

    def _determine_preference(
        self, preferences: RoutePreferences
    ) -> Literal["fastest", "shortest", "recommended"]:
        """Determine route preference based on user preferences.

        Args:
            preferences: User route preferences.

        Returns:
            ORS preference parameter.
        """
        if preferences.prefer_scenic:
            return "recommended"
        elif preferences.difficulty == "easy":
            return "shortest"
        else:
            return "fastest"

    def _parse_response(
        self, data: dict, preferences: RoutePreferences
    ) -> list[RouteSegment]:
        """Parse OpenRouteService response into route segments.

        Args:
            data: Response from OpenRouteService API.
            preferences: User preferences for surface type estimation.

        Returns:
            List of route segments.
        """
        features = data.get("features", [])
        if not features:
            raise RouteGenerationError("No route found in API response")

        feature = features[0]
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})

        # Get coordinates (ORS returns [lng, lat] or [lng, lat, elevation])
        raw_coords = geometry.get("coordinates", [])
        coordinates = [
            (coord[1], coord[0]) for coord in raw_coords  # (lat, lng)
        ]

        # Get segments from instructions
        segments_data = properties.get("segments", [])
        if not segments_data:
            # Create single segment if no segment data
            return [self._create_single_segment(coordinates, properties, preferences)]

        # Process multiple segments
        segments = []
        for seg_data in segments_data:
            segment = self._create_segment_from_data(seg_data, coordinates, preferences)
            segments.append(segment)

        return segments

    def _create_single_segment(
        self, coordinates: list[tuple[float, float]], properties: dict, preferences: RoutePreferences
    ) -> RouteSegment:
        """Create a single route segment from full route data.

        Args:
            coordinates: List of (lat, lng) coordinates.
            properties: Route properties from API.
            preferences: User preferences.

        Returns:
            A single route segment.
        """
        summary = properties.get("summary", {})
        distance_km = summary.get("distance", 0) / 1000.0  # meters to km
        duration_min = int(summary.get("duration", 0) / 60.0)  # seconds to minutes

        # Calculate elevation gain/loss if available
        ascent = properties.get("ascent", 0)
        descent = properties.get("descent", 0)

        # Estimate surface type based on preferences and route type
        surface_type = self._estimate_surface_type(properties, preferences)

        return RouteSegment(
            coordinates=coordinates,
            distance_km=distance_km,
            elevation_gain_m=ascent,
            elevation_loss_m=descent,
            estimated_duration_min=duration_min,
            surface_type=surface_type,
        )

    def _create_segment_from_data(
        self, seg_data: dict, all_coordinates: list[tuple[float, float]], preferences: RoutePreferences
    ) -> RouteSegment:
        """Create route segment from segment data.

        Args:
            seg_data: Segment data from API.
            all_coordinates: All route coordinates.
            preferences: User preferences.

        Returns:
            Route segment.
        """
        steps = seg_data.get("steps", [])
        distance_km = seg_data.get("distance", 0) / 1000.0
        duration_min = int(seg_data.get("duration", 0) / 60.0)
        ascent = seg_data.get("ascent", 0)
        descent = seg_data.get("descent", 0)

        # Extract coordinates for this segment
        # This is simplified - in production would need proper index mapping
        segment_coords = all_coordinates  # Fallback to all coordinates

        surface_type = self._estimate_surface_type(seg_data, preferences)

        return RouteSegment(
            coordinates=segment_coords,
            distance_km=distance_km,
            elevation_gain_m=ascent,
            elevation_loss_m=descent,
            estimated_duration_min=duration_min,
            surface_type=surface_type,
        )

    def _estimate_surface_type(
        self, properties: dict, preferences: RoutePreferences
    ) -> str:
        """Estimate surface type from route properties.

        Args:
            properties: Route or segment properties.
            preferences: User preferences.

        Returns:
            Surface type: "paved", "gravel", or "dirt".
        """
        # Check if extra_info contains surface data
        extras = properties.get("extras", {})
        surface_info = extras.get("surface", {})

        if surface_info:
            # ORS surface types: 0=Unknown, 1=Paved, 2=Unpaved, 3=Asphalt, etc.
            values = surface_info.get("values", [])
            if values:
                # Take most common surface type
                surface_code = values[0][2] if len(values[0]) > 2 else 0
                if surface_code in [1, 3]:  # Paved or Asphalt
                    return "paved"
                elif surface_code == 2:  # Unpaved
                    return "gravel"

        # Fallback based on difficulty preference
        if preferences.difficulty == "hard":
            return "gravel"
        else:
            return "paved"
