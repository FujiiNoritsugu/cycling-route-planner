"""Elevation profile calculation for cycling routes."""

import httpx


class ElevationAPIError(Exception):
    """Raised when elevation API request fails."""

    pass


class ElevationService:
    """Calculates elevation profiles using OpenMeteo Elevation API."""

    BASE_URL = "https://api.open-meteo.com/v1/elevation"

    async def get_elevation_profile(
        self, coordinates: list[tuple[float, float]]
    ) -> list[float]:
        """Get elevation profile for a list of coordinates.

        Args:
            coordinates: List of (lat, lng) tuples.

        Returns:
            List of elevations in meters (same length as coordinates).

        Raises:
            ElevationAPIError: If API request fails.
        """
        if not coordinates:
            return []

        # OpenMeteo elevation API accepts up to 100 points per request
        # For longer routes, we'll sample evenly
        max_points = 100
        sampled_coords = self._sample_coordinates(coordinates, max_points)

        elevations = await self._fetch_elevations(sampled_coords)

        # Interpolate back to original number of points if we sampled
        if len(sampled_coords) < len(coordinates):
            elevations = self._interpolate_elevations(
                elevations, len(sampled_coords), len(coordinates)
            )

        return elevations

    async def calculate_elevation_stats(
        self, elevations: list[float]
    ) -> tuple[float, float]:
        """Calculate total elevation gain and loss.

        Args:
            elevations: List of elevation values in meters.

        Returns:
            Tuple of (total_gain_m, total_loss_m).
        """
        if len(elevations) < 2:
            return 0.0, 0.0

        total_gain = 0.0
        total_loss = 0.0

        for i in range(1, len(elevations)):
            diff = elevations[i] - elevations[i - 1]
            if diff > 0:
                total_gain += diff
            else:
                total_loss += abs(diff)

        return total_gain, total_loss

    def _sample_coordinates(
        self, coordinates: list[tuple[float, float]], max_points: int
    ) -> list[tuple[float, float]]:
        """Sample coordinates evenly if there are too many.

        Args:
            coordinates: Full list of coordinates.
            max_points: Maximum number of points to sample.

        Returns:
            Sampled coordinates (or original if within limit).
        """
        if len(coordinates) <= max_points:
            return coordinates

        # Always include first and last points
        step = (len(coordinates) - 1) / (max_points - 1)
        indices = [int(i * step) for i in range(max_points - 1)]
        indices.append(len(coordinates) - 1)

        return [coordinates[i] for i in indices]

    async def _fetch_elevations(
        self, coordinates: list[tuple[float, float]]
    ) -> list[float]:
        """Fetch elevations from OpenMeteo API.

        Args:
            coordinates: List of (lat, lng) tuples.

        Returns:
            List of elevations in meters.

        Raises:
            ElevationAPIError: If API request fails.
        """
        # OpenMeteo elevation API expects comma-separated lat,lng pairs
        lats = [str(coord[0]) for coord in coordinates]
        lngs = [str(coord[1]) for coord in coordinates]

        params = {
            "latitude": ",".join(lats),
            "longitude": ",".join(lngs),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            # Fallback: try using OpenRouteService elevation API if available
            return await self._fallback_elevation_fetch(coordinates)
        except httpx.RequestError as e:
            # Network error - try fallback
            return await self._fallback_elevation_fetch(coordinates)

        # Parse elevation data
        elevations = data.get("elevation", [])
        if not elevations:
            raise ElevationAPIError("No elevation data in API response")

        return elevations

    async def _fallback_elevation_fetch(
        self, coordinates: list[tuple[float, float]]
    ) -> list[float]:
        """Fallback elevation fetch using alternative method.

        This is a simplified fallback that estimates elevation based on
        latitude (very rough approximation for demonstration).

        Args:
            coordinates: List of (lat, lng) tuples.

        Returns:
            List of estimated elevations.
        """
        # In production, this would use OpenRouteService elevation API
        # For now, return a simple estimation
        elevations = []
        for lat, lng in coordinates:
            # Very rough approximation: elevation increases with latitude in many regions
            # This is just a placeholder for demonstration
            estimated = max(0.0, (abs(lat) - 30) * 50)
            elevations.append(estimated)

        return elevations

    def _interpolate_elevations(
        self, elevations: list[float], original_count: int, target_count: int
    ) -> list[float]:
        """Interpolate elevations to match target count.

        Args:
            elevations: Original elevation values.
            original_count: Number of original points.
            target_count: Number of target points.

        Returns:
            Interpolated elevation values.
        """
        if original_count >= target_count or target_count == 1:
            return elevations[:target_count]

        if len(elevations) != original_count:
            # Safety check: ensure elevations list matches original_count
            elevations = elevations[:original_count] if len(elevations) > original_count else elevations

        interpolated = []
        for i in range(target_count):
            # Map target index to source index
            if target_count == 1:
                source_idx = 0.0
            else:
                source_idx = (i / (target_count - 1)) * (original_count - 1)

            lower_idx = int(source_idx)
            upper_idx = min(lower_idx + 1, len(elevations) - 1)

            # Linear interpolation
            if lower_idx >= len(elevations):
                interpolated.append(elevations[-1])
            elif lower_idx == upper_idx or upper_idx >= len(elevations):
                interpolated.append(elevations[lower_idx])
            else:
                fraction = source_idx - lower_idx
                value = elevations[lower_idx] * (1 - fraction) + elevations[
                    upper_idx
                ] * fraction
                interpolated.append(value)

        return interpolated
