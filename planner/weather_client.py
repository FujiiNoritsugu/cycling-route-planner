"""Weather forecasting using OpenMeteo API."""

from datetime import datetime, timedelta
import httpx
from planner.schemas import WeatherForecast, Location


class WeatherAPIError(Exception):
    """Raised when weather API request fails."""

    pass


class WeatherClient:
    """Fetches weather forecasts using OpenMeteo API (no API key required)."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # WMO Weather interpretation codes
    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    async def get_forecast(
        self,
        location: Location,
        start_time: datetime,
        hours: int = 24,
    ) -> list[WeatherForecast]:
        """Get weather forecast for a location.

        Args:
            location: Location to get forecast for.
            start_time: Start time for forecast.
            hours: Number of hours to forecast (default: 24).

        Returns:
            List of weather forecasts.

        Raises:
            WeatherAPIError: If API request fails.
        """
        params = {
            "latitude": location.lat,
            "longitude": location.lng,
            "hourly": [
                "temperature_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation_probability",
                "weather_code",
            ],
            "forecast_days": min(7, (hours // 24) + 1),
            "timezone": "auto",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            raise WeatherAPIError(
                f"OpenMeteo API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise WeatherAPIError(f"Failed to connect to OpenMeteo: {e}") from e

        return self._parse_forecast(data, start_time, hours)

    async def get_route_forecast(
        self,
        locations: list[Location],
        start_time: datetime,
        duration_hours: int,
    ) -> list[WeatherForecast]:
        """Get weather forecast along a route.

        Samples weather at key locations along the route and interpolates
        based on time of arrival at each location.

        Args:
            locations: List of locations along the route.
            start_time: Route start time.
            duration_hours: Expected route duration in hours.

        Returns:
            List of weather forecasts along the route.

        Raises:
            WeatherAPIError: If API requests fail.
        """
        if not locations:
            return []

        # Sample up to 5 locations along the route
        sample_count = min(5, len(locations))
        step = max(1, len(locations) // sample_count)
        sample_locations = locations[::step]

        # Get forecast for each location
        all_forecasts = []
        for i, location in enumerate(sample_locations):
            # Calculate approximate time at this location
            time_offset = (duration_hours / len(sample_locations)) * i
            location_time = start_time + timedelta(hours=time_offset)

            forecasts = await self.get_forecast(
                location, location_time, hours=duration_hours
            )
            all_forecasts.extend(forecasts)

        # Remove duplicates and sort by time
        unique_forecasts = {f.time: f for f in all_forecasts}
        return sorted(unique_forecasts.values(), key=lambda f: f.time)

    def _parse_forecast(
        self, data: dict, start_time: datetime, hours: int
    ) -> list[WeatherForecast]:
        """Parse OpenMeteo API response into WeatherForecast objects.

        Args:
            data: API response data.
            start_time: Start time for filtering forecasts.
            hours: Number of hours to include.

        Returns:
            List of weather forecasts.
        """
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        wind_directions = hourly.get("wind_direction_10m", [])
        precip_probs = hourly.get("precipitation_probability", [])
        weather_codes = hourly.get("weather_code", [])

        forecasts = []
        end_time = start_time + timedelta(hours=hours)

        # Make start_time and end_time timezone-aware if they aren't
        if start_time.tzinfo is None:
            from datetime import timezone
            start_time_aware = start_time.replace(tzinfo=timezone.utc)
            end_time_aware = end_time.replace(tzinfo=timezone.utc)
        else:
            start_time_aware = start_time
            end_time_aware = end_time

        for i, time_str in enumerate(times):
            # Parse time (ISO 8601 format)
            time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

            # Filter to requested time range
            if time < start_time_aware or time > end_time_aware:
                continue

            # Extract values (handle missing data)
            temperature = temperatures[i] if i < len(temperatures) else 0.0
            wind_speed = wind_speeds[i] if i < len(wind_speeds) else 0.0
            wind_direction = wind_directions[i] if i < len(wind_directions) else 0.0
            precip_prob = precip_probs[i] if i < len(precip_probs) else 0.0
            weather_code = int(weather_codes[i]) if i < len(weather_codes) else 0

            forecast = WeatherForecast(
                time=time,
                temperature=temperature,
                wind_speed=wind_speed,
                wind_direction=wind_direction,
                precipitation_probability=precip_prob,
                weather_code=weather_code,
                description=self._get_weather_description(weather_code),
            )
            forecasts.append(forecast)

        return forecasts

    def _get_weather_description(self, code: int) -> str:
        """Get human-readable description for WMO weather code.

        Args:
            code: WMO weather code.

        Returns:
            Weather description string.
        """
        return self.WEATHER_CODES.get(code, f"Unknown (code {code})")
