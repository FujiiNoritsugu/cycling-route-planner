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

    # WMO Weather interpretation codes (Japanese)
    WEATHER_CODES = {
        0: "快晴",
        1: "晴れ",
        2: "一部曇り",
        3: "曇り",
        45: "霧",
        48: "霧氷",
        51: "小雨",
        53: "雨",
        55: "強い霧雨",
        56: "小雨（凍結）",
        57: "強い霧雨（凍結）",
        61: "弱い雨",
        63: "雨",
        65: "強い雨",
        66: "弱い雨（凍結）",
        67: "強い雨（凍結）",
        71: "弱い雪",
        73: "雪",
        75: "強い雪",
        77: "霰",
        80: "弱いにわか雨",
        81: "にわか雨",
        82: "激しいにわか雨",
        85: "弱いにわか雪",
        86: "にわか雪",
        95: "雷雨",
        96: "雷雨（軽い雹）",
        99: "雷雨（強い雹）",
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
        # Ensure start_time is timezone-aware
        from datetime import timezone
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

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
            "timezone": "UTC",  # Request UTC timezone to match our datetime objects
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

        # Ensure start_time is timezone-aware
        from datetime import timezone
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        # Use a representative location (middle of route) for weather forecast
        # to avoid duplicates and provide relevant weather along the route
        if len(locations) == 1:
            representative_location = locations[0]
        else:
            # Use middle location
            mid_index = len(locations) // 2
            representative_location = locations[mid_index]

        # Get forecast for the representative location covering the entire route duration
        forecasts = await self.get_forecast(
            representative_location,
            start_time,
            hours=duration_hours
        )

        return forecasts

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

        # start_time should already be timezone-aware (converted in get_forecast/get_route_forecast)
        # Calculate end_time
        end_time = start_time + timedelta(hours=hours)

        for i, time_str in enumerate(times):
            # Parse time (ISO 8601 format)
            # OpenMeteo may return times without timezone suffix even when timezone=UTC
            if time_str.endswith("Z"):
                time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            elif "+" in time_str or time_str.count("-") > 2:  # Has timezone offset
                time = datetime.fromisoformat(time_str)
            else:
                # No timezone info, assume UTC (since we requested timezone=UTC)
                from datetime import timezone as tz
                time = datetime.fromisoformat(time_str).replace(tzinfo=tz.utc)

            # Filter to requested time range
            if time < start_time or time > end_time:
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
