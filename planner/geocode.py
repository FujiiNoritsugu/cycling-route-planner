"""Geocoding using OpenRouteService API."""

import os
import httpx
from planner.schemas import Location


class GeocodingError(Exception):
    """Raised when geocoding fails."""

    pass


class Geocoder:
    """Geocodes addresses using OpenRouteService API."""

    BASE_URL = "https://api.openrouteservice.org/geocode/search"

    def __init__(self, api_key: str | None = None):
        """Initialize the geocoder.

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

    async def geocode(self, query: str, country: str = "JP") -> list[Location]:
        """Geocode an address or place name.

        Args:
            query: Address or place name to geocode.
            country: Country code for filtering results (default: JP for Japan).

        Returns:
            List of matching locations (up to 5 results).

        Raises:
            GeocodingError: If geocoding fails.
        """
        if not query or not query.strip():
            raise GeocodingError("Query cannot be empty")

        params = {
            "api_key": self.api_key,
            "text": query.strip(),
            "boundary.country": country,
            "size": 5,  # Return up to 5 results
        }

        headers = {
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            raise GeocodingError(
                f"OpenRouteService Geocoding API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise GeocodingError(
                f"Failed to connect to OpenRouteService: {e}"
            ) from e

        # Parse response
        return self._parse_response(data)

    def _parse_response(self, data: dict) -> list[Location]:
        """Parse OpenRouteService geocoding response.

        Args:
            data: Response from OpenRouteService Geocoding API.

        Returns:
            List of locations.

        Raises:
            GeocodingError: If no results found.
        """
        features = data.get("features", [])
        if not features:
            raise GeocodingError("No results found for the given query")

        locations = []
        for feature in features:
            geometry = feature.get("geometry", {})
            properties = feature.get("properties", {})

            coordinates = geometry.get("coordinates", [])
            if len(coordinates) < 2:
                continue

            # ORS returns [lng, lat]
            lng, lat = coordinates[0], coordinates[1]

            # Get place name
            name = properties.get("label") or properties.get("name") or "Unknown"

            locations.append(
                Location(
                    lat=lat,
                    lng=lng,
                    name=name,
                )
            )

        if not locations:
            raise GeocodingError("No valid locations found in response")

        return locations
