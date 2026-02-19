"""Risk assessment and gear recommendations for cycling routes."""

from planner.schemas import RouteSegment, WeatherForecast, RoutePreferences


class RiskAssessor:
    """Assesses route risks and recommends appropriate gear."""

    # Risk thresholds
    HIGH_WIND_THRESHOLD = 10.0  # m/s
    VERY_HIGH_WIND_THRESHOLD = 15.0  # m/s
    HIGH_PRECIP_THRESHOLD = 50.0  # %
    VERY_HIGH_PRECIP_THRESHOLD = 70.0  # %
    COLD_TEMP_THRESHOLD = 5.0  # °C
    HOT_TEMP_THRESHOLD = 35.0  # °C
    HARD_ELEVATION_THRESHOLD = 2000.0  # m
    MODERATE_ELEVATION_THRESHOLD = 1000.0  # m
    LONG_DISTANCE_THRESHOLD = 100.0  # km

    def assess_route(
        self,
        segments: list[RouteSegment],
        weather_forecasts: list[WeatherForecast],
        preferences: RoutePreferences,
    ) -> tuple[list[str], list[str]]:
        """Assess route risks and generate warnings and gear recommendations.

        Args:
            segments: Route segments.
            weather_forecasts: Weather forecasts along the route.
            preferences: User preferences.

        Returns:
            Tuple of (warnings, recommended_gear).
        """
        warnings = []
        gear = set()  # Use set to avoid duplicates

        # Basic gear
        gear.add("Helmet")
        gear.add("Water bottles (at least 2)")
        gear.add("Repair kit (spare tube, tire levers, pump)")
        gear.add("Bike lights (front and rear)")

        # Assess weather risks
        weather_warnings, weather_gear = self._assess_weather(weather_forecasts)
        warnings.extend(weather_warnings)
        gear.update(weather_gear)

        # Assess elevation risks
        elevation_warnings, elevation_gear = self._assess_elevation(segments, preferences)
        warnings.extend(elevation_warnings)
        gear.update(elevation_gear)

        # Assess distance risks
        distance_warnings, distance_gear = self._assess_distance(segments)
        warnings.extend(distance_warnings)
        gear.update(distance_gear)

        # Assess surface type risks
        surface_warnings, surface_gear = self._assess_surface(segments)
        warnings.extend(surface_warnings)
        gear.update(surface_gear)

        return warnings, sorted(list(gear))

    def _assess_weather(
        self, forecasts: list[WeatherForecast]
    ) -> tuple[list[str], list[str]]:
        """Assess weather-related risks.

        Args:
            forecasts: Weather forecasts.

        Returns:
            Tuple of (warnings, gear).
        """
        warnings = []
        gear = []

        if not forecasts:
            return warnings, gear

        # Calculate weather statistics
        max_wind = max(f.wind_speed for f in forecasts)
        avg_wind = sum(f.wind_speed for f in forecasts) / len(forecasts)
        max_precip = max(f.precipitation_probability for f in forecasts)
        avg_temp = sum(f.temperature for f in forecasts) / len(forecasts)
        min_temp = min(f.temperature for f in forecasts)
        max_temp = max(f.temperature for f in forecasts)

        # Wind warnings
        if max_wind >= self.VERY_HIGH_WIND_THRESHOLD:
            warnings.append(
                f"⚠️ SEVERE: Very high wind speeds expected (up to {max_wind:.1f} m/s). "
                "Consider postponing the ride."
            )
            gear.append("Windproof jacket")
            gear.append("Eye protection (glasses)")
        elif max_wind >= self.HIGH_WIND_THRESHOLD:
            warnings.append(
                f"⚠️ Moderate to high wind speeds expected (up to {max_wind:.1f} m/s). "
                "Crosswinds may affect stability."
            )
            gear.append("Windbreaker or wind vest")

        # Precipitation warnings
        if max_precip >= self.VERY_HIGH_PRECIP_THRESHOLD:
            warnings.append(
                f"⚠️ SEVERE: High chance of rain ({max_precip:.0f}%). "
                "Wet conditions expected throughout the ride."
            )
            gear.append("Full rain jacket and pants")
            gear.append("Waterproof shoe covers")
            gear.append("Fenders (if available)")
        elif max_precip >= self.HIGH_PRECIP_THRESHOLD:
            warnings.append(
                f"⚠️ Moderate chance of rain ({max_precip:.0f}%). "
                "Pack rain gear just in case."
            )
            gear.append("Packable rain jacket")
            gear.append("Waterproof bag for electronics")

        # Temperature warnings
        if min_temp < self.COLD_TEMP_THRESHOLD:
            warnings.append(
                f"⚠️ Cold temperatures expected (as low as {min_temp:.1f}°C). "
                "Dress in layers and protect extremities."
            )
            gear.append("Thermal base layer")
            gear.append("Leg warmers or tights")
            gear.append("Gloves (preferably insulated)")
            gear.append("Ear warmer or headband")

        if max_temp > self.HOT_TEMP_THRESHOLD:
            warnings.append(
                f"⚠️ High temperatures expected (up to {max_temp:.1f}°C). "
                "Stay hydrated and consider early morning start."
            )
            gear.append("Extra water bottles")
            gear.append("Sunscreen (SPF 30+)")
            gear.append("Sunglasses")
            gear.append("Lightweight, breathable clothing")

        # Check for severe weather codes
        severe_weather = [f for f in forecasts if f.weather_code >= 95]
        if severe_weather:
            warnings.append(
                "⚠️ SEVERE: Thunderstorms possible. Avoid riding during storms."
            )

        return warnings, gear

    def _assess_elevation(
        self, segments: list[RouteSegment], preferences: RoutePreferences
    ) -> tuple[list[str], list[str]]:
        """Assess elevation-related risks.

        Args:
            segments: Route segments.
            preferences: User preferences.

        Returns:
            Tuple of (warnings, gear).
        """
        warnings = []
        gear = []

        total_elevation_gain = sum(seg.elevation_gain_m for seg in segments)

        # Check against user's max elevation preference
        if preferences.max_elevation_gain_m:
            if total_elevation_gain > preferences.max_elevation_gain_m:
                warnings.append(
                    f"⚠️ Total elevation gain ({total_elevation_gain:.0f}m) exceeds "
                    f"your preference ({preferences.max_elevation_gain_m:.0f}m)."
                )

        # General elevation warnings
        if total_elevation_gain >= self.HARD_ELEVATION_THRESHOLD:
            warnings.append(
                f"⚠️ Very challenging elevation gain ({total_elevation_gain:.0f}m). "
                "This route is suitable for experienced cyclists only."
            )
            gear.append("Extra energy gels or bars")
            gear.append("Electrolyte supplements")

            # Check difficulty mismatch
            if preferences.difficulty in ["easy", "moderate"]:
                warnings.append(
                    f"⚠️ Route difficulty may not match '{preferences.difficulty}' preference. "
                    "Consider an alternative route."
                )

        elif total_elevation_gain >= self.MODERATE_ELEVATION_THRESHOLD:
            warnings.append(
                f"Moderate elevation gain ({total_elevation_gain:.0f}m). "
                "Maintain a steady pace and take breaks as needed."
            )
            gear.append("Energy bars or snacks")

        # Check for steep segments
        steep_segments = [
            (i, seg)
            for i, seg in enumerate(segments)
            if seg.distance_km > 0 and (seg.elevation_gain_m / (seg.distance_km * 1000)) > 0.08
        ]

        if steep_segments:
            steepest = max(
                steep_segments,
                key=lambda x: x[1].elevation_gain_m / (x[1].distance_km * 1000),
            )
            idx, seg = steepest
            gradient = (seg.elevation_gain_m / (seg.distance_km * 1000)) * 100
            warnings.append(
                f"⚠️ Steep climb in segment {idx + 1}: {gradient:.1f}% gradient. "
                "Consider lower gearing."
            )

        return warnings, gear

    def _assess_distance(self, segments: list[RouteSegment]) -> tuple[list[str], list[str]]:
        """Assess distance-related risks.

        Args:
            segments: Route segments.

        Returns:
            Tuple of (warnings, gear).
        """
        warnings = []
        gear = []

        total_distance = sum(seg.distance_km for seg in segments)

        if total_distance >= self.LONG_DISTANCE_THRESHOLD:
            warnings.append(
                f"Long distance ride ({total_distance:.1f}km). "
                "Plan for rest stops and ensure adequate nutrition."
            )
            gear.append("Multiple energy bars or gels")
            gear.append("Electrolyte drink mix")
            gear.append("Emergency cash/card for resupply")
            gear.append("Portable phone charger")

        # Recommend based on duration
        total_duration = sum(seg.estimated_duration_min for seg in segments)
        if total_duration > 180:  # More than 3 hours
            gear.append("Chamois cream (for comfort)")
            gear.append("Arm warmers (temperature changes)")

        return warnings, gear

    def _assess_surface(self, segments: list[RouteSegment]) -> tuple[list[str], list[str]]:
        """Assess surface type risks.

        Args:
            segments: Route segments.

        Returns:
            Tuple of (warnings, gear).
        """
        warnings = []
        gear = []

        # Calculate surface distribution
        surface_km = {}
        for seg in segments:
            surface_km[seg.surface_type] = (
                surface_km.get(seg.surface_type, 0) + seg.distance_km
            )

        total_distance = sum(surface_km.values())

        # Check for unpaved surfaces
        gravel_km = surface_km.get("gravel", 0)
        dirt_km = surface_km.get("dirt", 0)
        unpaved_km = gravel_km + dirt_km

        if unpaved_km > 0:
            unpaved_pct = (unpaved_km / total_distance) * 100
            if unpaved_pct > 50:
                warnings.append(
                    f"⚠️ Majority of route is unpaved ({unpaved_pct:.0f}%). "
                    "Gravel or mountain bike recommended."
                )
                gear.append("Wider tires (28mm+ or gravel tires)")
                gear.append("Extra spare tube")
            elif unpaved_pct > 20:
                warnings.append(
                    f"Significant unpaved sections ({unpaved_pct:.0f}%). "
                    "Ensure tires are suitable for mixed terrain."
                )
                gear.append("All-terrain or gravel tires")

        return warnings, gear

    def calculate_risk_score(
        self,
        segments: list[RouteSegment],
        weather_forecasts: list[WeatherForecast],
    ) -> float:
        """Calculate overall risk score (0-100, higher = more risky).

        Args:
            segments: Route segments.
            weather_forecasts: Weather forecasts.

        Returns:
            Risk score between 0 and 100.
        """
        risk_score = 0.0

        # Weather risk (0-40 points)
        if weather_forecasts:
            max_wind = max(f.wind_speed for f in weather_forecasts)
            max_precip = max(f.precipitation_probability for f in weather_forecasts)
            max_temp = max(f.temperature for f in weather_forecasts)
            min_temp = min(f.temperature for f in weather_forecasts)

            # Wind risk (0-15)
            risk_score += min(15, max_wind / self.VERY_HIGH_WIND_THRESHOLD * 15)

            # Precipitation risk (0-15)
            risk_score += max_precip / 100 * 15

            # Temperature risk (0-10)
            if min_temp < self.COLD_TEMP_THRESHOLD:
                risk_score += min(10, (self.COLD_TEMP_THRESHOLD - min_temp) / 5 * 10)
            if max_temp > self.HOT_TEMP_THRESHOLD:
                risk_score += min(10, (max_temp - self.HOT_TEMP_THRESHOLD) / 10 * 10)

        # Elevation risk (0-30 points)
        total_elevation = sum(seg.elevation_gain_m for seg in segments)
        risk_score += min(30, total_elevation / self.HARD_ELEVATION_THRESHOLD * 30)

        # Distance risk (0-20 points)
        total_distance = sum(seg.distance_km for seg in segments)
        risk_score += min(20, total_distance / 150 * 20)

        # Surface risk (0-10 points)
        unpaved_km = sum(
            seg.distance_km for seg in segments if seg.surface_type in ["gravel", "dirt"]
        )
        total_km = sum(seg.distance_km for seg in segments)
        if total_km > 0:
            risk_score += (unpaved_km / total_km) * 10

        return min(100.0, risk_score)
